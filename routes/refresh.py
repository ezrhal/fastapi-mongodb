
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from config.config import settings
from security.security import create_token

router = APIRouter()

ACCESS_TOKEN_EXPIRE_MINUTES = 3
REFRESH_TOKEN_EXPIRE_DAYS = 1

