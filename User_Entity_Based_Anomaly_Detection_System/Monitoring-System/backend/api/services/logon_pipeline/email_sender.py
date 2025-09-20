import asyncio
from types import SimpleNamespace
from sqlalchemy.orm import Session
import smtplib
from core.config import settings
import anyio, ssl
from email.message import EmailMessage

# 디버깅 용 임포트 
from model.database import SessionLocal, engine, get_db, Base

from model.security_manager import models as SecurityManager_models
from model.security_manager import crud as security_manager_crud
from model.security_manager import schemas as security_manager_schemas

from model.organization import models as Organization_models
from model.organization import crud as organization_crud
from model.organization import schemas as organization_schemas

from model.functional_unit import models as FunctionalUnit_models
from model.functional_unit import crud as functional_unit_crud

from model.department import models as Department_models    
from model.department import crud as department_crud

from model.team import models as Team_models
from model.team import crud as team_crud

from model.employee import models as Employee_models
from model.employee import crud as employee_crud

from model.pc import models as Pc_models
from model.pc import crud as pc_crud
from model.pc import schemas as pc_schemas

from model.router import models as Router_models
from model.router import crud as router_crud
from model.router import schemas as router_schemas

from model.behavior_log import models as BehaviorLog_models
from model.behavior_log import crud as behavior_log_crud
from model.behavior_log import schemas as behavior_logs_schemas
from model.behavior_log.init_behavior_log import BehaviorLogInserter

from model.anomaly_detection_history import models as AnomalyDetectionHistory_models
from model.anomaly_detection_history import crud as anomaly_detection_history_crud  

from model.blocking_history import models as BlockingHistory_models 
from model.security_manager.crud import get_security_manager_emails_by_oid

class EmailSender:
    def __init__(self, db: Session, log_data, organization_id: str):
        self.db = db
        self.log_data = log_data
        self.organization_id = organization_id

    async def run(self):
        email_list = self.get_managers_email()  
        if not email_list:
            print("No managers found for the organization.")
            return
        subject, body, body_html = self._compose_email_content()

        for email in email_list:
            await self.send_email(email, subject, body, body_html)

    def get_managers_email(self):
        return get_security_manager_emails_by_oid(self.db, self.organization_id)

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: str):
        def _send_sync():
            msg = EmailMessage()
            msg["From"] = settings.EMAIL_SENDER
            msg["To"] = to_email
            msg["Subject"] = subject

            # 텍스트(폴백) + HTML(리치)
            msg.set_content(body_text or " ")                              # text/plain
            if body_html:
                msg.add_alternative(body_html, subtype="html")             # text/html

            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
                s.ehlo()
                s.starttls(context=context)
                s.ehlo()
                s.login(settings.EMAIL_SENDER, settings.EMAIL_SENDER_PASSWORD)
                s.send_message(msg)

        # smtplib는 동기 라이브러리 → 이벤트 루프 블로킹 방지
        await anyio.to_thread.run_sync(_send_sync)

    def _compose_email_content(self):
        subject = f"🚨 Sentra 경보 | 악성 의심 사용자 로그온 감지 — 차단 조치 완료 ({self.log_data.pc_id})"

        body_text = (
            f"[ALERT]\n"
            f"악성 의심 사용자 {self.log_data.employee_id} 가 PC {self.log_data.pc_id} 에 로그온했습니다.\n"
            f"시간: {self.log_data.timestamp}\n"
            f"> 네트워크 차단 조치가 자동으로 수행되었습니다."
        )

        body_html = f"""
        <div style="font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;max-width:640px;margin:0 auto;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden">
        <!-- 헤더/배너 -->
        <div style="background:#b91c1c;color:#fff;padding:16px 20px">
            <div style="font-size:18px;font-weight:700">🚨 경보: 악성 의심 사용자 로그온 감지</div>
            <div style="opacity:.9;font-size:12px">Sentra Security • 자동 차단 조치 완료</div>
        </div>

        <!-- 본문 -->
        <div style="padding:20px">
            <p style="margin:0 0 12px 0;font-size:14px;line-height:1.6">
            아래 사용자 로그온 이벤트가 탐지되었으며,
            <span style="font-weight:700;color:#b91c1c">해당 PC에 대한 네트워크 차단(Access Block)이 자동으로 수행되었습니다.</span>
            </p>

            <!-- 상태 배지 -->
            <div style="margin:12px 0 16px 0">
            <span style="display:inline-block;background:#991b1b;color:#fff;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700;letter-spacing:.2px">
                BLOCKED
            </span>
            <span style="display:inline-block;background:#fef3c7;color:#92400e;border-radius:999px;padding:4px 10px;font-size:12px;margin-left:6px">
                ANOMALY DETECTED
            </span>
            </div>

            <!-- 상세 정보 -->
            <table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;font-size:14px">
            <tbody>
                <tr>
                <td style="width:140px;color:#6b7280;padding:8px 0">User ID</td>
                <td style="padding:8px 0"><b>{self.log_data.employee_id}</b></td>
                </tr>
                <tr>
                <td style="color:#6b7280;padding:8px 0">PC ID</td>
                <td style="padding:8px 0"><b>{self.log_data.pc_id}</b></td>
                </tr>
                <tr>
                <td style="color:#6b7280;padding:8px 0">Time</td>
                <td style="padding:8px 0">{self.log_data.timestamp}</td>
                </tr>
            </tbody>
            </table>

            <!-- 안내 -->
            <div style="margin-top:16px;padding:12px 14px;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;color:#991b1b;font-size:13px;line-height:1.5">
            차단 해제는 관리자 승인 하에서만 수행하십시오. 재발 방지를 위해 사용자·단말 행위 로그를 즉시 검토해 주세요.
            </div>

            <!-- 액션 버튼 (링크 있으면 href 교체) -->
            <div style="margin-top:18px">
            <a href="#" style="display:inline-block;background:#111827;color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;font-size:13px">
                대시보드에서 이벤트 확인
            </a>
            <a href="#" style="display:inline-block;color:#111827;text-decoration:underline;margin-left:12px;font-size:13px">
                차단 정책 보기
            </a>
            </div>

            <!-- 푸터 -->
            <p style="margin:18px 0 0 0;color:#6b7280;font-size:12px">
            본 메일은 Sentra Security에 의해 자동 발송되었습니다.
            </p>
        </div>
        </div>
        """
        return subject, body_text, body_html

# 디버깅용 테스트 코드
# async def _main():
#     db = SessionLocal()              
#     try:
#         log_data = SimpleNamespace(employee_id="CCA0046", pc_id="PC-8865", timestamp="2025-08-29 18:00:00")
#         sender = EmailSender(db, log_data, "9d1b2dcb-662e-4185-9007-d7e23d5abbf7")
#         await sender.run()
#     finally:
#         db.close()

# if __name__ == "__main__":
#     asyncio.run(_main())