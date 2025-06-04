import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base
from app.chat_service import ChatService
from app.config import get_settings

# Create tables
Base.metadata.create_all(bind=engine)

settings = get_settings()
chat_service = ChatService()


def create_sample_documents():
    """Create sample HR documents if they don't exist"""
    docs_path = settings.hr_docs_path
    os.makedirs(docs_path, exist_ok=True)
    
    sample_docs = {
        "pto-policy.txt": """PTO (Paid Time Off) Policy

Employees accrue 15 days of PTO per year, which increases to 20 days after 3 years of service and 25 days after 5 years.

PTO can be used for vacation, personal time, or sick leave. Employees must request PTO at least 2 weeks in advance for vacation time, except in cases of emergency or illness.

Unused PTO can be carried over to the next year, up to a maximum of 10 days. Any PTO above this limit will be forfeited at the end of the year.

Upon termination, employees will be paid out for any accrued but unused PTO.""",
        
        "benefits-guide.txt": """Employee Benefits Guide

Health Insurance:
- We offer comprehensive health insurance through Blue Cross Blue Shield
- Coverage includes medical, dental, and vision
- Company covers 80% of employee premiums and 50% of dependent premiums
- Open enrollment occurs annually in November

401(k) Retirement Plan:
- Company matches 100% of the first 3% of salary contributed
- Additional 50% match on the next 2% of salary contributed
- Immediate vesting of company contributions
- Wide variety of investment options available

Life Insurance:
- Basic life insurance equal to 2x annual salary provided at no cost
- Additional voluntary life insurance available for purchase

Other Benefits:
- Flexible Spending Account (FSA) for healthcare and dependent care
- Employee Assistance Program (EAP)
- Gym membership reimbursement up to $50/month
- Professional development budget of $1,500/year""",
        
        "remote-work-policy.txt": """Remote Work Policy

Eligible employees may work remotely up to 3 days per week, subject to manager approval. 

Requirements:
- Reliable internet connection (minimum 25 Mbps)
- Dedicated workspace free from distractions
- Available during core hours (10 AM - 3 PM in your time zone)
- Attend all required meetings via video conference

Equipment:
- Company will provide laptop and necessary software
- $500 one-time stipend for home office setup
- Monthly internet reimbursement of $50

Expectations:
- Maintain same productivity levels as in-office work
- Respond to communications within 2 hours during work hours
- Use company-approved tools for communication and collaboration
- Ensure data security and confidentiality

Remote work privileges may be revoked if performance standards are not met.""",
        
        "expense-policy.txt": """Expense Reimbursement Policy

Business Travel:
- All business travel must be pre-approved by your manager
- Book flights at least 14 days in advance when possible
- Economy class for flights under 4 hours, premium economy for longer flights
- Hotel stays should not exceed $200/night without approval

Meals:
- Breakfast: up to $20
- Lunch: up to $30
- Dinner: up to $50
- Alcohol is not reimbursable

Ground Transportation:
- Use company-preferred vendors when available
- Taxi/rideshare for short distances
- Rental cars require pre-approval

Submission:
- Submit expense reports within 30 days of expense
- Include all receipts
- Use company expense management system
- Reimbursement typically processed within 2 weeks""",
        
        "training-resources.txt": """Professional Development and Training

Annual Training Budget:
- Each employee has $1,500 annual budget for professional development
- Unused budget does not roll over to next year

Approved Training Types:
- Online courses and certifications
- Professional conferences and workshops
- Industry-relevant books and materials
- Professional association memberships

Internal Training:
- Monthly lunch-and-learn sessions
- Mentorship program available
- Access to LinkedIn Learning for all employees
- Internal knowledge sharing platform

Approval Process:
- Submit training request through HR portal
- Include cost, duration, and relevance to role
- Manager approval required for all requests
- HR approval required for amounts over $500

Time for Training:
- Up to 40 hours per year for approved training during work hours
- Additional training must be completed on personal time"""
    }
    
    for filename, content in sample_docs.items():
        filepath = os.path.join(docs_path, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created sample document: {filename}")
        else:
            print(f"Document already exists: {filename}")


def ingest_all_documents():
    """Ingest all documents in the HR docs folder"""
    db = SessionLocal()
    docs_path = settings.hr_docs_path
    
    if not os.path.exists(docs_path):
        print(f"Documents folder not found: {docs_path}")
        return
    
    for filename in os.listdir(docs_path):
        if filename.endswith('.txt'):
            filepath = os.path.join(docs_path, filename)
            print(f"Ingesting document: {filename}")
            
            try:
                result = chat_service.ingest_document(db, filepath, filename)
                print(f"  Status: {result['status']}")
                if result['status'] == 'success':
                    print(f"  Chunks created: {result['chunks']}")
            except Exception as e:
                print(f"  Error: {str(e)}")
    
    db.close()


if __name__ == "__main__":
    print("Creating sample HR documents...")
    create_sample_documents()
    
    print("\nIngesting documents into vector database...")
    # Note: This will fail if Pinecone index doesn't exist or OpenAI key is not set
    # For demo purposes, we'll just create the documents
    try:
        ingest_all_documents()
    except Exception as e:
        print(f"Note: Document ingestion requires valid API keys and vector database setup")
        print(f"Error: {str(e)}")
    
    print("\nSetup complete!")