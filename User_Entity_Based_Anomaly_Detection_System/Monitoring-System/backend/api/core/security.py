from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi_jwt_auth import AuthJWT
import os
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "fdasssssssssssssssssssssss1233213213123123123jn12qewjnsdn")
@AuthJWT.load_config
def get_config():
    return Settings()

# 비밀번호 해시 생성을 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔑 해시 생성
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 🔒 해시 검증 (로그인 시 사용)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 인증 코드 해시 생성 (alias)
def get_auth_code_hash(code: str) -> str:
    return get_password_hash(code)

# 인증 코드 검증
def verify_auth_code(input_code: str, hashed_code: str) -> bool:
    return verify_password(input_code, hashed_code)