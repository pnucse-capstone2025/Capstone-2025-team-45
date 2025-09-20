from pydantic import BaseSettings, BaseModel
import os
class Settings(BaseSettings):
    #App Settings
    PROJECT_NAME: str = 'Sentra - API'
    APP_NAME: str = "Monitoring System - Backend"
    API_STR: str = "/api/v1"
    PROWLER_API_STR: str = "/api/prowler"

    #프론트엔드 URL (CORS 허용을 위해)
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    # Database configuration
    # 데이터베이스 설정
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5433'))
    DB_NAME: str = os.getenv('DB_NAME', 'Sentra_DB')
    DB_USER: str = os.getenv('DB_USER', 'sentra_user')  
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'huni5504')  # Changed from PASSWORD to DB_PASSWORD
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    #JWT Settings
    #JWT 토큰 설정
    SECRET_KEY: str = '26mpViW3rldpRIrlqhPlzXSqbMscYMd8MCJHk6ipxus3YzAGXPS2PGQl2FqjDEyxH5OAHmFEAThkyGXJYetG1iY0byF32Slc6Tv3AHRtStHWec9UwK9HdSHQL2V0c5w94GzcAxlqg9udRcZ3tMwlLdMF63BZefU0TCYHBbmksI8vXIUXqc9LbxigEXpGG5GQjd009DxVGAEXU40yMJdCgX3mkJjDBtl4XM0Sa29HfWhdk8fL6I6Jdk5w5Krbd3Ie'
    TOKEN_LOCATION: set = {'cookies'}
    CSRF_PROTECT: bool = False
    COOKIE_SECURE: bool = False  # should be True in production
    COOKIE_SAMESITE: str = 'lax'  # should be 'lax' or 'strict' in production
    ACCESS_TOKEN_EXPIRES: int = 900  # 15 minutes = 900
    REFRESH_TOKEN_EXPIRES: int = 2592000  # 30 days = 2592000
    
    # ADMIN Settings
    # 사이트 관리자 계정 정보
    ADMIN_USERID: str = 'admin'
    ADMIN_USERNAME: str = 'kwanghun lee'
    ADMIN_EMAIL: str = 'gbhuni@gmail.com'
    ADMIN_PASSWORD: str = 'huni5504'
    ADMIN_COMPANY_NAME: str = 'SkyForge Systems'

    #기본 조직 정보
    ADMIN_COMPANY_NAME: str = 'SkyForge Systems'
    ADMIN_AUTH_CODE: str = '1234567890123456'  # 16 characters long
    ADMIN_ORGANIZATION_DESCRIPTION: str = '하이브리드 클라우드 환경에 맞춘 DevOps 자동화 및 보안 정책 관리 툴을 제공하는 기업. 대규모 인프라 운영 기업을 주요 고객으로 한다.'

    #추가 조직 정보
    ADDITIONAL_ORGANIZATIONS_NAME: str = 'Samsung Electronics'
    ADDITIONAL_ORGANIZATIONS_AUTH_CODE: str = 'samsung123456789'  # 16 characters long
    ADDITIONAL_ORGANIZATIONS_DESCRIPTION: str = '삼성전자는 글로벌 전자제품 및 반도체 기업으로, 혁신적인 기술과 제품을 통해 세계 시장에서 선도적인 위치를 차지하고 있습니다.'

    # 관리자 계정에 이메일을 전송하기 위한 계정 
    EMAIL_SENDER: str = 'gbhuni@gmail.com'
    EMAIL_SENDER_PASSWORD: str = 'ldss ycha hwvz wvlg'
    

settings = Settings()