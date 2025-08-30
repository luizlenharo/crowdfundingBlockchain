How to run: 

1. Install the dependencies
   cd backend
   pip install -r requirements.txt

2. Setup blockchain config
   python ./setup.py

3. Run backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

4. Run frontend
   cd frontend
   python -m http.server 3000
