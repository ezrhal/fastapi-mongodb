from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from config.config import settings
from config.db.pmis_db import pmis_session
from config.db.dts_db import dts_session

from sqlalchemy import text
import time

from security.security import create_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

ACCESS_TOKEN_EXPIRE_MINUTES = 1440
REFRESH_TOKEN_EXPIRE_DAYS = 5


## region LOGIN

@router.post("/login")
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends(),
                pmissession: AsyncSession = Depends(pmis_session),
                dtssession: AsyncSession = Depends(dts_session)
                ):
    """
    OAuth2 Password flow: send x-www-form-urlencoded body:
      username, password
    Returns: { access_token, token_type, refresh_token }
    """

    username = form.username.split("@")[0]
    username = username + "@pgas.ph"
    password = form.password


    sql = text("select a.eid, a.firstname, a.lastname, b.emailaddress, c.Department, c.OfficeAbbr, c.OfficeName from employee a " +
        "join vwLoginParameter b on b.eid = a.eid " +
        "join vwMergeAllEmployee c on c.eid = a.eid where lower(b.emailaddress) = :username and passcode = :password")

    result = await pmissession.execute(sql, {"username": username, "password": password})

    user = result.mappings().one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Incorrect username or password")

    sql = text("select a.eid, menu, parentid, sort, icon, roleid from a_user_menu_vw a " +
            "join a_permission b on b.eid = a.eid where a.eid = :eid")

    result = await dtssession.execute(sql, {"eid": user.eid})
    permission = result.mappings().all()

    if not permission:
        raise HTTPException(status_code=401, detail="Invalid dts Access")

    menus = [
        {
            "menu": r["menu"],
            "parentid": r["parentid"],
            "sort": r["sort"],
            "icon": r["icon"],
        }
        for r in permission
    ]

    access = create_token(
        subject=user.emailaddress,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )

    refresh = create_token(
        subject=user.emailaddress,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh"
    )

    response.delete_cookie(key="refresh_token")

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True, secure=True, samesite="none",  # set secure+none if using across domains
        max_age= REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/auth"  # cookie only sent to /auth/*
    )


    return {"access_token": access, "token_type": "bearer", "user_login":
            {
                "roleid": permission[0].roleid,
                "eid": permission[0].eid,
                "name" : user.firstname,
                "officeid": user.Department,
                "menus" : menus
            }}

## endregion


## region REFRESH

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")

    if not token:
       response.delete_cookie("refresh_token", path="/auth")
       raise HTTPException(401, detail="refresh_expired")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=["HS256"],
            options={"verify_exp": True},  # explicit
            # leeway=0,                   # ensure no extra grace
        )
        if payload.get("type") != "refresh":
            raise HTTPException(401, detail="wrong_token_type")

        current_time = int(time.time())
        exp = payload.get("exp")
        print(str(current_time) + " " + str(exp))

        if current_time > exp:
            raise HTTPException(status_code=401, detail="Refresh token expired")

    except ExpiredSignatureError:
        response.delete_cookie("refresh_token", path="/auth")
        raise HTTPException(401, detail="refresh_expired")
    except JWTError:
        raise HTTPException(401, detail="invalid_refresh_token")

    sub = payload["sub"]

    # (Optional) rotate refresh token
    # new_refresh = make_token(sub, REFRESH_DAYS * 24 * 60, "refresh")
    # response.set_cookie(
    #     key="refresh_token",
    #     value=new_refresh,
    #     httponly=True, secure=True, samesite="none",
    #     max_age=REFRESH_DAYS * 24 * 3600, path="/auth"
    # )

    access = create_token(
        subject=sub,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )
    return {"access_token": access, "token_type": "bearer"}

## endregion


