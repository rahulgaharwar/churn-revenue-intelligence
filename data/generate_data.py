import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_saas_telemetry(num_customers=5000, seed=42):
    np.random.seed(seed)
    random.seed(seed)

    company_prefixes = ["Apex", "Nexus", "Vertex", "Hyper", "Quantum", "Cloud", "Data", "Pulse", "Sync", "Omni", "Vanguard", "Titan", "Aero", "Cyber", "Strata", "Aura", "Nova", "Flux", "Zentis", "Orion"]
    company_suffixes = ["Labs", "Tech", "Systems", "HQ", "Networks", "Solutions", "AI", "Cloud", "Global", "Analytics", "Digital", "Flow", "Stack", "Dynamics", "Software"]

    companies = [f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}" for _ in range(num_customers)]
    customer_ids = [f"CUST-{10000 + i}" for i in range(num_customers)]
    
    # Plans and MRR
    plans = ["Basic", "Pro", "Enterprise"]
    plan_probs = [0.50, 0.35, 0.15]
    customer_plans = np.random.choice(plans, size=num_customers, p=plan_probs)
    
    base_mrr_map = {"Basic": 49, "Pro": 199, "Enterprise": 999}
    mrrs = []
    for plan in customer_plans:
        base = base_mrr_map[plan]
        variance = np.random.normal(0, base * 0.15)
        mrrs.append(max(20, round(base + variance, 2)))
        
    contract_types = []
    for plan in customer_plans:
        if plan == "Enterprise":
            contract_types.append(np.random.choice(["Annual", "Multi-Year"], p=[0.7, 0.3]))
        elif plan == "Pro":
            contract_types.append(np.random.choice(["Monthly", "Annual"], p=[0.5, 0.5]))
        else:
            contract_types.append(np.random.choice(["Monthly", "Annual"], p=[0.8, 0.2]))
            
    # Dates & Tenure
    today = datetime(2026, 7, 1)
    tenure_months = np.random.geometric(p=0.04, size=num_customers) + 1
    tenure_months = np.clip(tenure_months, 1, 48)
    
    signup_dates = [today - timedelta(days=int(m * 30.4)) for m in tenure_months]
    
    # Usage & Engagement Telemetry
    active_users = []
    login_freq_30d = []
    login_decay_rates = []
    feature_adoption = []
    support_tickets_90d = []
    avg_ticket_res_hrs = []
    payment_failures_12m = []
    nps_scores = []
    
    for i in range(num_customers):
        plan = customer_plans[i]
        
        if plan == "Enterprise":
            users = int(np.random.normal(45, 15))
        elif plan == "Pro":
            users = int(np.random.normal(12, 4))
        else:
            users = int(np.random.normal(3, 1.5))
        active_users.append(max(1, users))
        
        logins = int(np.random.normal(24, 8) * active_users[-1])
        login_freq_30d.append(max(0, logins))
        
        decay = np.random.normal(-0.08, 0.28)
        login_decay_rates.append(round(float(np.clip(decay, -0.9, 0.5)), 3))
        
        fa = np.random.normal(60, 22)
        feature_adoption.append(round(float(np.clip(fa, 5, 100)), 1))
        
        tickets = np.random.poisson(lam=2.8)
        support_tickets_90d.append(tickets)
        
        res_time = np.random.exponential(scale=22.0)
        avg_ticket_res_hrs.append(round(float(max(1.0, res_time)), 1))
        
        pf = np.random.choice([0, 1, 2, 3], p=[0.75, 0.15, 0.07, 0.03])
        payment_failures_12m.append(pf)
        
        nps = int(np.clip(np.random.normal(6.8, 2.5), 0, 10))
        nps_scores.append(nps)

    # Churn probability logit model calibrated for ~18-22% churn rate
    logit = (
        -0.45
        - 2.8 * np.array(login_decay_rates)
        + 0.16 * (np.array(support_tickets_90d) * np.array(avg_ticket_res_hrs) / 24.0)
        + 0.75 * np.array(payment_failures_12m)
        - 0.03 * np.array(feature_adoption)
        - 0.22 * np.array(nps_scores)
        + 0.55 * (np.array(contract_types) == "Monthly").astype(int)
        + 0.35 * (np.array(customer_plans) == "Basic").astype(int)
        - 0.60 * (np.array(customer_plans) == "Enterprise").astype(int)
    )
    
    churn_prob = 1 / (1 + np.exp(-logit))
    churn_status = (np.random.rand(num_customers) < churn_prob).astype(int)
    
    df = pd.DataFrame({
        "customer_id": customer_ids,
        "company_name": companies,
        "signup_date": [d.strftime("%Y-%m-%d") for d in signup_dates],
        "plan_tier": customer_plans,
        "contract_type": contract_types,
        "mrr": mrrs,
        "tenure_months": tenure_months,
        "active_users": active_users,
        "login_frequency_30d": login_freq_30d,
        "login_decay_rate": login_decay_rates,
        "feature_adoption_score": feature_adoption,
        "support_tickets_90d": support_tickets_90d,
        "avg_ticket_res_hrs": avg_ticket_res_hrs,
        "payment_failures_12m": payment_failures_12m,
        "nps_score": nps_scores,
        "churn_status": churn_status
    })
    
    return df

if __name__ == "__main__":
    df = generate_saas_telemetry(num_customers=5000)
    output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "saas_churn_telemetry.csv")
    df.to_csv(file_path, index=False)
    print(f"[SUCCESS] Synthetic dataset generated with {len(df)} rows. Saved to: {file_path}")
    print(f"Churn rate: {df['churn_status'].mean()*100:.2f}%")
    print(f"Total ARR: ${df['mrr'].sum()*12:,.2f}")
