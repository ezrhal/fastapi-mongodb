from collections import defaultdict
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config.db.spms_db import spms_session
from config.db.postgres import get_db

router = APIRouter()

@router.get("/calendar")
async def get_calendar(
    postgres_db: Session = Depends(get_db),          # sync Postgres session
    session: AsyncSession = Depends(spms_session),   # async MSSQL session
):
    # --- 1) MSSQL calendar query (unchanged) ---
    sql = text("""
        WITH a AS (
            SELECT 
                a.[id],
                CONVERT(varchar, DATEADD(HOUR, 10, CAST([date] AS datetime)), 25) AS start_date_time,
                CONVERT(varchar, DATEADD(HOUR, 22, CAST([date] AS datetime)), 25) AS end_date_time, 
                CONCAT(
                    ' - ', 
                    b.Activity,
                    CASE 
                        WHEN b.id = 5 THEN CONCAT(' [', ISNULL(sold_docs, '0'), ']  ')
                        WHEN b.id IN (6, 7) THEN CONCAT('  ', ' [', ISNULL(LTRIM(LastName), '-'), ']  ')
                        ELSE ' ' 
                    END,
                    CASE WHEN ROW_NUMBER() OVER (PARTITION BY trans_id, activity_id ORDER BY [date] DESC) != 1 THEN ' Moved ' ELSE '' END,
                    CASE WHEN b.id = 5 THEN d.buyers COLLATE SQL_Latin1_General_CP1_CI_AS ELSE '' END
                ) AS activity,
                'Procurement Schedule' AS type,
                CASE 
                    WHEN ISNULL(a.isDone, 0) = 1 THEN '#474747'
                    WHEN ROW_NUMBER() OVER (PARTITION BY trans_id, activity_id ORDER BY [date] DESC) != 1 THEN '#474747'
                    ELSE b.color 
                END AS color,
                CAST(trans_id AS varchar) AS trans_id
            FROM tbl_procurementCalendar AS a
            LEFT JOIN tbl_procurementactivities AS b ON b.id = a.activity_id 
            LEFT JOIN (
                SELECT COUNT(id) AS sold_docs, pr_id
                FROM [BAC_OrderPayment].[dbo].[tbl_transaction_info] 
                WHERE ActionCode = 1 AND isPaid = 1
                GROUP BY pr_id
            ) AS c ON c.pr_id = a.trans_id
            LEFT JOIN (
                SELECT 
                    pr_id,
                    CONCAT('</br><ul class=''suplier_list''><li>',
                           STRING_AGG(supplier_name, '</li><li>') WITHIN GROUP (ORDER BY supplier_name ASC),
                           '</li></ul>') AS buyers  
                FROM [BAC_OrderPayment].[dbo].[tbl_transaction_info] 
                WHERE ActionCode = 1 AND isPaid = 1
                GROUP BY pr_id 
            ) AS d ON d.pr_id = a.trans_id
            LEFT JOIN [fmis].[dbo].[tblCMS_CDClaimantDetails] AS e ON e.trnno = CAST(a.supplier_id AS bigint)
            WHERE YEAR([date]) = 2025 AND a.activity_id != 6
        ),
        x AS (
            SELECT 
                [date] AS start_date_time,
                [date] AS end_date_time,
                postquagroup,
                a.supplier_id,
                b.Activity,
                b.color,
                a.trans_id 
            FROM tbl_procurementCalendar AS a
            LEFT JOIN tbl_procurementactivities AS b ON b.id = a.activity_id
            WHERE YEAR([date]) = 2025 AND a.activity_id = 6
            GROUP BY postquagroup, b.Activity, a.supplier_id, b.color, a.trans_id, a.date
        ),
        b AS (
            SELECT 
                0 AS id,
                CONVERT(varchar, DATEADD(HOUR, 8, CAST(a.start_date_time AS datetime)), 25) AS start_date_time,
                CONVERT(varchar, DATEADD(HOUR, 17, CAST(a.end_date_time AS datetime)), 25) AS end_date_time,
                CONCAT(' - ', a.Activity, ' @ </br><ul class=''suplier_list''>',
                       STRING_AGG(CONCAT('<li>', b.LastName COLLATE SQL_Latin1_General_CP1_CI_AS, '</li>'), ''),
                       '</ul>') AS activity,
                'Procurement Schedule' AS [type],
                a.color,
                STRING_AGG(CAST(a.trans_id AS varchar), ',') AS trans_id 
            FROM x AS a
            LEFT JOIN [fmis].[dbo].[tblCMS_CDClaimantDetails] AS b ON b.trnno = CAST(a.supplier_id AS bigint)
            GROUP BY a.start_date_time, end_date_time, a.Activity, a.color
        )
        SELECT * FROM a
        UNION
        SELECT * FROM b;
    """)

    result = await session.execute(sql)
    mssql_rows = result.mappings().all()  # List[RowMapping]

    # --- 2) Collect all trans_id values (handles comma-separated strings) ---
    def _parse_trans_ids(val: Any) -> List[int]:
        if val is None:
            return []
        out: List[int] = []
        for part in str(val).split(","):
            s = part.strip()
            if s:
                out.append(int(s))  # if your IDs are text, drop the int(...)
        return out

    all_prids = {
        pid
        for row in mssql_rows
        for pid in _parse_trans_ids(row["trans_id"])
    }

    # If no PRs found, return MSSQL rows with empty items
    if not all_prids:
        return [{**dict(r), "items": []} for r in mssql_rows]

    # --- 3) Postgres query (single round-trip, parameterized IN with expanding) ---
    pg_sql = text("""
        SELECT 
            a.prid,
            CONCAT(transno, ' ', prno) AS transno,
            item,
            brand,
            description,
            unit,
            quantity,
            unitcost,
            quantity*unitcost AS totalcost,
            TO_CHAR(c.totalamount,'FM999,999,999.00') AS totalamount
        FROM t_pr a
        LEFT JOIN t_pr_items b      ON b.prid = a.prid AND b.isactive = '1'
        LEFT JOIN t_pr_amount1_vw c ON c.prid = a.prid
        WHERE a.prid IN :ids
    """).bindparams(bindparam("ids", expanding=True))

    pg_rows = postgres_db.execute(pg_sql, {"ids": list(all_prids)}).mappings().all()

    # --- 4) Group Postgres items by prid ---
    items_by_prid: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for r in pg_rows:
        items_by_prid[int(r["prid"])].append(dict(r))

    # --- 5) Attach items to each MSSQL row (merging across multiple trans_id per row) ---
    # --- 5) Attach items to each MSSQL row as an HTML table ---
    enriched = []
    for row in mssql_rows:
        row_dict = dict(row)
        prids_for_row = _parse_trans_ids(row_dict.get("trans_id"))

        # Collect all items for this row
        merged_items: List[Dict[str, Any]] = []
        for pid in prids_for_row:
            merged_items.extend(items_by_prid.get(pid, []))

        if merged_items:
            # Build HTML table
            html_parts = [
                "<table class='t_procurement_items' style='width:100%;'>",
                "<tr>"
                "<th>No.</th>"
                "<th>Item</th>"
                "<th>Brand</th>"
                "<th>Description</th>"
                "<th>Unit</th>"
                "<th>Quantity</th>"
                "</tr>",
            ]
            for i, item in enumerate(merged_items, start=1):
                html_parts.append(
                    f"<tr>"
                    f"<td>{i}</td>"
                    f"<td>{item.get('item', '')}</td>"
                    f"<td>{item.get('brand', '')}</td>"
                    f"<td>{item.get('description', '')}</td>"
                    f"<td>{item.get('unit', '')}</td>"
                    f"<td>{item.get('quantity', '')}</td>"
                    f"</tr>"
                )
            html_parts.append("</table>")
            row_dict["items"] = "".join(html_parts)
        else:
            row_dict["items"] = ""  # no items

        enriched.append(row_dict)

    return enriched
