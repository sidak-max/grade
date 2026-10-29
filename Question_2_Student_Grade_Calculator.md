# Question 2: Student Grade Calculator — Kubernetes CI/CD Pipeline

## Requirements

- Create a Python application in VS Code.
- Use the five stages: Source Code, Version Control, Continuous Integration, Build, and Deployment.
- Push 1: Calculate total and average marks.
- Push 2: Add grade calculation based on the average.
- Make exactly two source-code pushes from VS Code to GitHub.
- Use a unique Docker image tag for each push.
- GitHub Actions must test the code, build the Docker image, and push it to Docker Hub.
- Deploy each version to Kubernetes and expose it through a Service.

## 1. Check prerequisites

Install and start VS Code, Git, Python 3.12 or compatible Python 3, Docker Desktop with Kubernetes enabled, `kubectl`, a GitHub account, and a Docker Hub account.

Open VS Code → Terminal → New Terminal. Run:

```powershell
git --version
python --version
docker --version
docker info
kubectl version --client
kubectl get nodes
```

Proceed only when Docker works and the Kubernetes node shows `Ready`.

## 2. Create the project

Create a folder named `student-grade-calculator` and open it in VS Code. Create this structure:

```text
student-grade-calculator/
├── app.py
├── requirements.txt
├── test_app.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
└── .github/
    └── workflows/
        └── pipeline.yml
```

## 3. Create the application for Push 1

### 3.1 `app.py`

This version calculates total and average only.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return """
        <h2>Student Grade Calculator</h2>
        <form method="post">
            <label>Marks (comma-separated):</label>
            <input name="marks" required>
            <button type="submit">Calculate</button>
        </form>
        """
    try:
        marks = [float(value.strip()) for value in request.form["marks"].split(",")]
        if not marks or any(mark < 0 or mark > 100 for mark in marks):
            return "Enter marks between 0 and 100.", 400
        total = sum(marks)
        average = total / len(marks)
        return jsonify(total=round(total, 2), average=round(average, 2))
    except (ValueError, KeyError):
        return "Enter valid comma-separated marks.", 400

@app.route("/health")
def health():
    return jsonify(status="healthy"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 3.2 `requirements.txt`

```text
Flask>=3.0,<4.0
pytest>=8.0,<9.0
```

### 3.3 `test_app.py`

```python
from app import app

def test_total_and_average():
    client = app.test_client()
    response = client.post("/", data={"marks": "80,90,70"})
    assert response.status_code == 200
    assert response.json["total"] == 240
    assert response.json["average"] == 80

def test_invalid_marks():
    client = app.test_client()
    response = client.post("/", data={"marks": "80,120"})
    assert response.status_code == 400

def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
```

## 4. Add Docker and Git ignore files

### 4.1 `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 4.2 `.dockerignore`

```text
.venv/
__pycache__/
.pytest_cache/
.git/
```

### 4.3 `.gitignore`

```text
.venv/
__pycache__/
.pytest_cache/
.env
```

## 5. Test Push 1 locally

Run in the VS Code PowerShell terminal from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: all three tests pass.

Start the application:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000/`, enter `80,90,70`, and submit.

Expected result:

```json
{"average":80.0,"total":240.0}
```

Stop the server with `Ctrl+C`.

## 6. Create GitHub and Docker Hub repositories

1. Create a **public** GitHub repository named `student-grade-calculator`. Do not initialize it with a README.
2. Create a **public** Docker Hub repository named `student-grade-calculator`.
3. In Docker Hub, create an access token with permission to push images. Keep it secure.

## 7. Configure GitHub Actions secrets

In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.

Add:

| Secret name | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Your Docker Hub access token |

Do not put credentials in source files or YAML.

## 8. Create the CI/CD workflow

Create `.github/workflows/pipeline.yml`:

```yaml
name: Student Grade Calculator CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    name: Checkout and Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout source code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run automated tests
        run: python -m pytest -v

  docker:
    name: Build and Push Docker Image
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Checkout source code
        uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - name: Build and push image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/student-grade-calculator:${{ github.sha }}
```

The image tag is the commit SHA, so each source push gets a unique image tag.

## 9. Create Kubernetes deployment files

### 9.1 `k8s/deployment.yaml`

Replace `YOUR_DOCKERHUB_USERNAME` and `REPLACE_WITH_PUSH_1_SHA` with your actual Docker Hub username and the commit SHA for Push 1.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: student-grade-calculator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: student-grade-calculator
  template:
    metadata:
      labels:
        app: student-grade-calculator
    spec:
      containers:
        - name: student-grade-calculator
          image: YOUR_DOCKERHUB_USERNAME/student-grade-calculator:REPLACE_WITH_PUSH_1_SHA
          ports:
            - containerPort: 5000
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
```

### 9.2 `k8s/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: student-grade-calculator
spec:
  type: NodePort
  selector:
    app: student-grade-calculator
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30080
```

## 10. Make Push 1

Replace `YOUR_GITHUB_USERNAME` with your GitHub username. Run from the project folder:

```powershell
git init
git add .
git commit -m "Push 1: Add total and average calculator"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/student-grade-calculator.git
git push -u origin main
```

This is **Push 1**. Do not make another source-code push until the Push 2 changes are ready.

### 10.1 Verify the pipeline and image

1. Open the GitHub repository and select **Actions**.
2. Open the latest workflow run.
3. Confirm `Checkout and Test` and `Build and Push Docker Image` both pass.
4. Open Docker Hub and copy the full commit SHA tag produced by this run.

Update the image field in `k8s/deployment.yaml` to use that exact Push 1 tag.

## 11. Deploy Push 1 to Kubernetes

Run from the project directory:

```powershell
kubectl config current-context
kubectl get nodes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl rollout status deployment/student-grade-calculator
kubectl get deployments
kubectl get pods
kubectl get services
```

Wait until both replicas are ready.

Open `http://localhost:30080/`. Enter marks such as `80,90,70`.

Expected result:

```json
{"average":80.0,"total":240.0}
```

Check `http://localhost:30080/health`.

## 12. Modify the application for Push 2

Replace `app.py` with this version. The grade scale below is used for this practical: A for average >= 90, B for >= 80, C for >= 70, D for >= 60, otherwise F.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

def calculate_grade(average):
    if average >= 90:
        return "A"
    if average >= 80:
        return "B"
    if average >= 70:
        return "C"
    if average >= 60:
        return "D"
    return "F"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return """
        <h2>Student Grade Calculator</h2>
        <form method="post">
            <label>Marks (comma-separated):</label>
            <input name="marks" required>
            <button type="submit">Calculate</button>
        </form>
        """
    try:
        marks = [float(value.strip()) for value in request.form["marks"].split(",")]
        if not marks or any(mark < 0 or mark > 100 for mark in marks):
            return "Enter marks between 0 and 100.", 400
        total = sum(marks)
        average = total / len(marks)
        grade = calculate_grade(average)
        return jsonify(total=round(total, 2), average=round(average, 2), grade=grade)
    except (ValueError, KeyError):
        return "Enter valid comma-separated marks.", 400

@app.route("/health")
def health():
    return jsonify(status="healthy"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

Replace `test_app.py` with:

```python
from app import app

def test_total_average_and_grade():
    client = app.test_client()
    response = client.post("/", data={"marks": "80,90,70"})
    assert response.status_code == 200
    assert response.json["total"] == 240
    assert response.json["average"] == 80
    assert response.json["grade"] == "B"

def test_grade_boundaries():
    client = app.test_client()
    assert client.post("/", data={"marks": "90"}).json["grade"] == "A"
    assert client.post("/", data={"marks": "80"}).json["grade"] == "B"
    assert client.post("/", data={"marks": "70"}).json["grade"] == "C"
    assert client.post("/", data={"marks": "60"}).json["grade"] == "D"
    assert client.post("/", data={"marks": "59"}).json["grade"] == "F"

def test_invalid_marks():
    client = app.test_client()
    response = client.post("/", data={"marks": "80,120"})
    assert response.status_code == 400

def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"
```

Run the tests before Push 2:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: all four tests pass.

## 13. Make Push 2

Run:

```powershell
git add app.py test_app.py
git commit -m "Push 2: Add grade calculation"
git push
```

This is **Push 2**. Do not make any additional source-code pushes for this assessment.

## 14. Verify Push 2 and deploy the updated version

1. Open GitHub **Actions**.
2. Open the latest workflow run and confirm both jobs pass.
3. Copy the new commit SHA used as the Docker image tag.
4. In `k8s/deployment.yaml`, replace the image tag with the Push 2 SHA.

Run:

```powershell
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/student-grade-calculator
kubectl get pods
kubectl get deployment student-grade-calculator
```

Test `http://localhost:30080/` with marks `80,90,70`.

Expected result:

```json
{"average":80.0,"grade":"B","total":240.0}
```

The JSON key order may differ.

Open `http://localhost:30080/health`. Expected response:

```json
{"status":"healthy"}
```

## 15. Final verification checklist

- [ ] Push 1 calculates total and average.
- [ ] Push 1 workflow tests pass and publishes a uniquely tagged Docker image.
- [ ] Push 1 image is deployed to Kubernetes.
- [ ] Kubernetes Deployment has two ready replicas.
- [ ] Service is available at `http://localhost:30080/`.
- [ ] Push 2 adds grade calculation based on the average.
- [ ] Push 2 workflow tests pass and publishes a different, uniquely tagged Docker image.
- [ ] Kubernetes Deployment is updated to the Push 2 image.
- [ ] The updated version returns total, average, and grade.
- [ ] Exactly two source-code pushes were made from VS Code to GitHub.
