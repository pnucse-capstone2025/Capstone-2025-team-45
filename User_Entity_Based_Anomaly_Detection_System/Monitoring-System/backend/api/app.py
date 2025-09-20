from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

from model.init_database import init_database
from model.database import engine, SessionLocal
from core.config import settings

print(
"""   
======================================        
 _____               _                
/  ___|             | |               
\ `--.   ___  _ __  | |_  _ __   __ _ 
 `--. \ / _ \| '_ \ | __|| '__| / _` |
/\__/ /|  __/| | | || |_ | |   | (_| |
\____/  \___||_| |_| \__||_|    \__,_|
 S  E  N  T  R  A  •  S E C U R I T Y
======================================                                 
""")

try:
    init_database(engine, SessionLocal())
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("The API will start but database operations may fail until connection is established")
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json",
    debug=True,
)

# CORS
origins = ["http://localhost:3000", "http://localhost:3001", "http://172.23.164.185:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 라우터 등록 ----
from api.v1 import auth, organizations, topology, anomaly_detect, network_access_control, pcs, behavior_logs
from api.v1.router import network_monitor, log_collector

auth_header = APIKeyHeader(name="Authorization", auto_error=False)
deps = [Depends(auth_header)]  # HTTP 라우터에만 적용

api_prefix = settings.API_STR.rstrip("/")  # '/api/v1'
# 인증 필요 없는 라우터 (예: 로그인/토큰발급)
app.include_router(auth.router, prefix=api_prefix, tags=["auth"])

# 인증 필요한 HTTP 라우터들만 deps 부여
app.include_router(organizations.router,        prefix=api_prefix, tags=["Organizations"],      dependencies=deps)
app.include_router(topology.router,             prefix=api_prefix, tags=["Topology"],           dependencies=deps)
app.include_router(anomaly_detect.router,       prefix=api_prefix, tags=["Anomaly Detect"],     dependencies=deps)
app.include_router(network_access_control.router,prefix=api_prefix, tags=["Network Access Control"], dependencies=deps)
app.include_router(pcs.router,                  prefix=api_prefix, tags=["PC"],                 dependencies=deps)
app.include_router(behavior_logs.router,        prefix=api_prefix, tags=["Behavior Logs"],      dependencies=deps)
app.include_router(network_monitor.router,      prefix=api_prefix, tags=["Network Monitor"],    dependencies=deps)
app.include_router(log_collector.router,        prefix=api_prefix, tags=["Log Collector"],      dependencies=deps)

# ---- WebSocket (의존성 없이) ----
from api.v1.websocket import alerts as ws_alerts
app.include_router(ws_alerts.router, prefix=api_prefix, tags=["WS"])