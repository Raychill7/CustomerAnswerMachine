from locust import HttpUser, between, task


class ChatUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def chat(self) -> None:
        self.client.post(
            "/chat",
            json={
                "session_id": "load-test",
                "user_message": "请问发票怎么开",
                "user_id": "u-load",
            },
        )
