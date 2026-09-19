FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN useradd --create-home --uid 10001 finplan \
    && mkdir -p /home/finplan/.config/finplan-tui \
    && chown -R finplan:finplan /app /home/finplan
USER finplan

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "app.py"]
CMD ["--demo"]
