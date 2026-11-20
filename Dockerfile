# Web game in a container (the browser does the 3D rendering; the server needs only the standard library).
FROM python:3.12-slim
WORKDIR /app
COPY *.py *.html game.contract.json ./
EXPOSE 8787
CMD ["python", "server_preview.py", "--host", "0.0.0.0", "--port", "8787"]
