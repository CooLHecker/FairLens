"""
generate_samples.py  —  Generate all sample CSVs for testing FairLens
Run: python generate_samples.py
"""
import numpy as np
import pandas as pd

np.random.seed(42)

# ── 1. Hiring CSV ─────────────────────────────────────────────────────────────
def gen_hiring(n=300):
    genders  = np.random.choice(["Male","Female","Non-binary"],n,p=[0.55,0.40,0.05])
    castes   = np.random.choice(["General","OBC","SC","ST"],n,p=[0.50,0.25,0.15,0.10])
    locs     = np.random.choice(["Metro","Tier-2","Rural"],n,p=[0.45,0.35,0.20])
    tiers    = np.random.choice([1,2,3],n,p=[0.20,0.45,0.35])
    edu      = np.random.choice([0,1,2,3],n,p=[0.05,0.55,0.30,0.10])
    exp      = np.clip(np.random.normal(4,3,n).astype(int),0,25)
    cgpa     = np.round(np.clip(np.random.normal(7.2,1.2,n),4.0,10.0),2)

    cgpa_n   = (cgpa-4)/6; exp_n = np.clip(exp/15,0,1); edu_n = edu/3
    skills   = np.round((0.4*cgpa_n+0.35*exp_n+0.25*edu_n)*100+np.random.normal(0,3,n),1).clip(0,100)
    is_qual  = ((skills>=50)&(edu>=1)&(cgpa>=6.0)).astype(int)

    base = 0.25+(skills-50)/200
    base[genders=="Female"]     *= 0.78
    base[genders=="Non-binary"] *= 0.65
    base[castes=="SC"]          *= 0.70
    base[castes=="ST"]          *= 0.62
    base[castes=="OBC"]         *= 0.85
    base[locs=="Rural"]         *= 0.72
    base[locs=="Tier-2"]        *= 0.88
    base[tiers==1]              *= 1.25
    base[tiers==3]              *= 0.80
    base = np.clip(base,0.02,0.95)
    sel  = (np.random.rand(n)<base).astype(int)

    df = pd.DataFrame({
        "candidate_id":   [f"C{i+1:04d}" for i in range(n)],
        "gender":         genders,"caste":castes,"location":locs,
        "college_tier":   tiers,"education_level":edu,
        "years_experience":exp,"skills_score":skills,
        "cgpa":cgpa,"is_qualified":is_qual,"selected":sel,
    })
    df.to_csv("sample_data/hiring.csv",index=False)
    print(f"✅  hiring.csv  ({n} rows)")
    return df


# ── 2. ML predictions CSV ─────────────────────────────────────────────────────
def gen_ml(hiring_df):
    df = hiring_df.copy()
    # Simulate a biased ML model: higher FPR for SC/ST, lower recall for Women
    prob = df["skills_score"]/100
    prob[df["gender"]=="Female"]  -= 0.12   # model penalises women
    prob[df["caste"].isin(["SC","ST"])] -= 0.15
    prob = prob.clip(0.05,0.95)

    ml = pd.DataFrame({
        "candidate_id":       df["candidate_id"],
        "gender":             df["gender"],
        "caste":              df["caste"],
        "location":           df["location"],
        "college_tier":       df["college_tier"],
        "education_level":    df["education_level"],
        "actual_label":       df["is_qualified"],
        "predicted_probability": prob.round(4),
        "predicted_label":    (prob>=0.50).astype(int),
    })
    ml.to_csv("sample_data/ml_predictions.csv",index=False)
    print(f"✅  ml_predictions.csv  ({len(ml)} rows)")


# ── 3. Manager CSV ────────────────────────────────────────────────────────────
def gen_manager(hiring_df):
    df   = hiring_df.copy()
    mgrs = np.random.choice([f"MGR{i:02d}" for i in range(1,11)],len(df))
    # MGR01 and MGR03 are biased against SC/ST
    for i,row in df.iterrows():
        if mgrs[i]=="MGR01" and row["caste"] in ["SC","ST"]:
            df.at[i,"selected"] = 0
        if mgrs[i]=="MGR03" and row["gender"]=="Female":
            df.at[i,"selected"] = 0

    mgr_df = df.copy()
    mgr_df["manager_id"]      = mgrs
    mgr_df["interview_score"] = np.round(np.clip(
        df["skills_score"]+np.random.normal(0,10,len(df)),0,100),1)

    mgr_df[["candidate_id","manager_id","gender","caste","location",
            "college_tier","education_level","interview_score","selected"]]\
        .to_csv("sample_data/manager.csv",index=False)
    print(f"✅  manager.csv  ({len(mgr_df)} rows)")


# ── 4. Leave CSV ──────────────────────────────────────────────────────────────
def gen_leave(n=400):
    genders = np.random.choice(["Male","Female"],n,p=[0.55,0.45])
    castes  = np.random.choice(["General","OBC","SC","ST"],n,p=[0.50,0.25,0.15,0.10])
    locs    = np.random.choice(["Metro","Tier-2","Rural"],n,p=[0.45,0.35,0.20])
    depts   = np.random.choice(["Engineering","Sales","HR","Finance","Ops"],n)
    l_type  = np.random.choice(["Sick","Casual","Annual","Maternity"],n,p=[0.3,0.3,0.3,0.1])
    days_r  = np.random.randint(1,21,n)

    # Bias: women get fewer days approved; SC/ST also penalised
    approval_base = np.ones(n)*0.85
    approval_base[genders=="Female"]         -= 0.18
    approval_base[castes=="SC"]              -= 0.15
    approval_base[castes=="ST"]              -= 0.22
    approval_base[l_type=="Maternity"]       -= 0.10   # extra bias against maternity
    approved  = (np.random.rand(n)<approval_base.clip(0.1,0.98)).astype(int)
    days_a    = np.where(approved, days_r*np.random.uniform(0.5,1.0,n), 0).astype(int)

    pd.DataFrame({
        "employee_id":   [f"E{i+1:04d}" for i in range(n)],
        "gender":genders,"caste":castes,"location":locs,"department":depts,
        "leave_type":l_type,"days_requested":days_r,
        "days_approved":days_a,"approved":approved,
    }).to_csv("sample_data/leave.csv",index=False)
    print(f"✅  leave.csv  ({n} rows)")


# ── 5. Task CSV ───────────────────────────────────────────────────────────────
def gen_task(n=300):
    genders   = np.random.choice(["Male","Female"],n,p=[0.55,0.45])
    castes    = np.random.choice(["General","OBC","SC","ST"],n,p=[0.50,0.25,0.15,0.10])
    locs      = np.random.choice(["Metro","Tier-2","Rural"],n,p=[0.45,0.35,0.20])
    depts     = np.random.choice(["Engineering","Sales","HR","Finance","Ops"],n)

    # Bias: men and General caste get more high-value tasks
    task_type = []
    promo     = []
    complexity= []
    for i in range(n):
        hv_prob = 0.40
        if genders[i]=="Male":        hv_prob += 0.15
        if castes[i]=="General":      hv_prob += 0.12
        if castes[i] in ["SC","ST"]:  hv_prob -= 0.15
        tt = np.random.choice(["high_value","routine","admin"],
                               p=[min(hv_prob,0.6),0.35,max(0.05,0.65-hv_prob)])
        task_type.append(tt)
        promo.append(1 if (tt=="high_value" and np.random.rand()<0.6) else 0)
        base_comp = 4.0 if tt=="high_value" else (2.5 if tt=="routine" else 1.5)
        complexity.append(round(np.clip(base_comp+np.random.normal(0,0.5),1,5),1))

    pd.DataFrame({
        "employee_id":         [f"E{i+1:04d}" for i in range(n)],
        "gender":genders,"caste":castes,"location":locs,"department":depts,
        "task_type":task_type,"task_count":np.random.randint(5,50,n),
        "avg_task_complexity":complexity,"promotion_track":promo,
    }).to_csv("sample_data/task.csv",index=False)
    print(f"✅  task.csv  ({n} rows)")


if __name__=="__main__":
    import os; os.makedirs("sample_data",exist_ok=True)
    hiring = gen_hiring()
    gen_ml(hiring)
    gen_manager(hiring)
    gen_leave()
    gen_task()
    print("\n✅  All sample CSVs generated in ./sample_data/")
