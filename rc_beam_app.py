# =============================================================
# RC Structure Optimizer — Streamlit Web App
# ครอบคลุม: คาน | เสา | พื้น
# ติดตั้ง: pip install streamlit pandas numpy
# รัน:     streamlit run rc_beam_app.py
# =============================================================

import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="RC Structure Optimizer", page_icon="🏗️", layout="wide")
st.title("🏗️ RC Structure Optimizer")
st.caption("วิเคราะห์และปรับแต่งโครงสร้างคอนกรีตเสริมเหล็ก — ACI 318")
st.divider()

# =============================================================
# ฟังก์ชันวัสดุร่วม
# =============================================================
def Ec(fc): return 4700 * np.sqrt(fc) * 1000   # kN/m²
def beta1(fc): return max(0.65, 0.85 - 0.05 * max(0, fc-28)/7)
def rho_min_beam(fc, fy): return max(0.25*np.sqrt(fc)/fy, 1.4/fy)

def util_bar(label, value, max_val=100):
    pct  = min(value / max_val * 100, 150) if max_val > 0 else 0
    icon = "🟢" if pct <= 80 else ("🟡" if pct <= 100 else "🔴")
    bar  = "█" * int(pct/5) + "░" * (30 - int(min(pct,150)/5))
    st.text(f"{icon} {label:16s} {bar} {value:.1f}%")

# =============================================================
# แท็บหลัก
# =============================================================
tab_beam, tab_col, tab_slab = st.tabs(["🔩 คาน (Beam)", "🏛️ เสา (Column)", "⬜ พื้น (Slab)"])

# ██████████████████████████████████████████████████████████████
# TAB 1: คาน
# ██████████████████████████████████████████████████████████████
with tab_beam:
    mode_b = st.radio("โหมด", ["🔧 Design — หา section จาก load",
                                "🔍 Check & Optimize — ตรวจสอบแบบที่มีอยู่"],
                      horizontal=True, key="mode_beam")
    st.divider()

    # ---------- ฟังก์ชันคาน ----------
    def beam_design(b_mm, h_mm, span, wdl, wll, fc, fy, cover_mm, bar_mm):
        b, h = b_mm/1000, h_mm/1000
        d    = h - cover_mm/1000 - (bar_mm/2)/1000
        w    = wdl + wll
        Ec_  = Ec(fc)
        A, I = b*h, b*h**3/12
        Mu, Vu = w*span**2/8, w*span/2
        dt = 5*w*span**4/(384*Ec_*I)*1000
        dl = 5*wll*span**4/(384*Ec_*I)*1000
        l240, l360 = span*1000/240, span*1000/360
        dok = dt<=l240 and dl<=l360
        if d<=0.05: return None
        Rn = (Mu*1e6)/(0.9*(b*1000)*(d*1000)**2)
        disc = 1-(2*Rn)/(0.85*fc)
        if disc<0: return None
        rho = max((0.85*fc/fy)*(1-np.sqrt(disc)), rho_min_beam(fc,fy))
        As  = rho*(b*1000)*(d*1000)
        a   = As*fy/(0.85*fc*b*1000)
        pMn = 0.9*As*fy*(d*1000-a/2)/1e6
        mok = pMn>=Mu
        Vc  = 0.17*np.sqrt(fc)*(b*1000)*(d*1000)/1000
        sok = 0.75*Vc>=Vu/2
        ok  = dok and mok and sok
        return {"Section":f"{b_mm}×{h_mm}","กว้าง":b_mm,"สูง":h_mm,
                "Mu(kN·m)":round(Mu,2),"Vu(kN)":round(Vu,2),
                "Defl(mm)":round(dt,3),"L/240":round(l240,2),
                "As(mm²)":round(As,1),"φMn(kN·m)":round(pMn,2),
                "φVc(kN)":round(0.75*Vc,2),
                "Deflection":"✅" if dok else "❌",
                "Moment":"✅" if mok else "❌",
                "Shear":"✅" if sok else "⚠️",
                "Overall":"✅ PASS" if ok else "❌ FAIL",
                "คอนกรีต(m³)":round(A*span,4),
                "_ok":ok,"_vol":A*span}

    def beam_check(b_mm,h_mm,n,bar_mm,span,wdl,wll,fc,fy,cover_mm):
        b,h = b_mm/1000,h_mm/1000
        d   = h-cover_mm/1000-(bar_mm/2)/1000
        w   = wdl+wll; Ec_=Ec(fc)
        As  = n*np.pi*(bar_mm/2)**2
        I   = b*h**3/12; A=b*h
        a   = As*fy/(0.85*fc*b*1000)
        pMn = 0.9*As*fy*(d*1000-a/2)/1e6
        Vc  = 0.17*np.sqrt(fc)*(b*1000)*(d*1000)/1000
        pVc = 0.75*Vc
        Mu,Vu = w*span**2/8, w*span/2
        dt  = 5*w*span**4/(384*Ec_*I)*1000
        dl  = 5*wll*span**4/(384*Ec_*I)*1000
        l240,l360 = span*1000/240,span*1000/360
        return {"pMn":round(pMn,2),"pVc":round(pVc,2),
                "Mu":round(Mu,2),"Vu":round(Vu,2),
                "util_M":round(Mu/pMn*100,1) if pMn>0 else 999,
                "util_V":round((Vu/2)/pVc*100,1) if pVc>0 else 999,
                "dt":round(dt,3),"l240":round(l240,2),
                "util_D":round(dt/l240*100,1),
                "w_max":round(min(pMn*8/span**2, pVc*2/span*2),2),
                "vol":round(A*span,4),
                "ok_M":pMn>=Mu,"ok_V":pVc>=Vu/2,
                "ok_D":dt<=l240 and dl<=l360}

    # ---------- BEAM: Design ----------
    if mode_b.startswith("🔧"):
        col_in, col_out = st.columns([1,3])
        with col_in:
            st.subheader("พารามิเตอร์")
            span = st.number_input("Span (m)",1.0,20.0,5.0,0.5,key="bs")
            wdl  = st.number_input("DL (kN/m)",0.0,200.0,10.0,1.0,key="bdl")
            wll  = st.number_input("LL (kN/m)",0.0,200.0,10.0,1.0,key="bll")
            fc   = st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="bfc")
            fy   = st.selectbox("fy",[ 250,390,500],index=1,key="bfy",
                                format_func=lambda x:f"SD{x}")
            cover   = st.number_input("Cover (mm)",20,75,40,5,key="bcv")
            bar_dia = st.number_input("DB เหล็กหลัก",12,32,20,2,key="bdb")
            secs_in = st.text_area("Section กว้าง,สูง (mm)",
                        "200,400\n250,500\n250,600\n300,600\n300,700\n350,700\n400,700\n400,800",
                        height=180,key="bsec")
            go = st.button("วิเคราะห์",type="primary",use_container_width=True,key="bgo")

        with col_out:
            if go:
                res=[]
                for ln in secs_in.strip().splitlines():
                    try:
                        p=ln.strip().replace("x",",").split(",")
                        r=beam_design(int(p[0]),int(p[1]),span,wdl,wll,fc,fy,cover,bar_dia)
                        if r: res.append(r)
                    except: pass
                if not res: st.error("ไม่มีข้อมูล"); st.stop()
                df=pd.DataFrame(res)
                passed=df[df["_ok"]]
                c1,c2,c3,c4=st.columns(4)
                c1.metric("Section ทั้งหมด",len(df))
                c2.metric("ผ่านเกณฑ์",len(passed))
                if not passed.empty:
                    best=passed.loc[passed["_vol"].idxmin()]
                    c3.metric("ประหยัดที่สุด",best["Section"])
                    c4.metric("คอนกรีต",f"{best['คอนกรีต(m³)']:.4f} m³")
                    st.success(f"✅ แนะนำ **{best['Section']} mm** | As={best['As(mm²)']} mm² | คอนกรีต {best['คอนกรีต(m³)']} m³")
                else: st.error("ไม่มี section ผ่านเกณฑ์")
                disp=[c for c in df.columns if not c.startswith("_")]
                st.dataframe(df[disp],use_container_width=True,hide_index=True)
                st.download_button("⬇️ CSV",df[disp].to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                                   f"beam_design.csv","text/csv",use_container_width=True)
            else: st.info("👈 ใส่ค่าแล้วกด วิเคราะห์")

    # ---------- BEAM: Check ----------
    else:
        col_in,col_out=st.columns([1,3])
        with col_in:
            st.subheader("แบบที่มีอยู่")
            b_mm=st.number_input("กว้าง (mm)",100,1000,300,50,key="ckb")
            h_mm=st.number_input("สูง (mm)",100,2000,700,50,key="ckh")
            span=st.number_input("Span (m)",1.0,20.0,5.0,0.5,key="cks")
            n_bars=st.number_input("จำนวนเหล็ก (เส้น)",1,20,4,1,key="ckn")
            bar_dia=st.selectbox("ขนาด DB",[12,16,20,25,28,32],index=2,key="ckdb")
            cover=st.number_input("Cover (mm)",20,75,40,5,key="ckcv")
            wdl=st.number_input("DL (kN/m)",0.0,200.0,10.0,1.0,key="ckdl")
            wll=st.number_input("LL (kN/m)",0.0,200.0,10.0,1.0,key="ckll")
            fc=st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="ckfc")
            fy=st.selectbox("fy",[250,390,500],index=1,key="ckfy",format_func=lambda x:f"SD{x}")
            go=st.button("ตรวจสอบ",type="primary",use_container_width=True,key="ckgo")

        with col_out:
            if go:
                r=beam_check(b_mm,h_mm,n_bars,bar_dia,span,wdl,wll,fc,fy,cover)
                ok_all=r["ok_M"] and r["ok_V"] and r["ok_D"]
                if ok_all: st.success(f"✅ Section {b_mm}×{h_mm} mm ผ่านทุกเกณฑ์")
                else: st.error(f"❌ Section {b_mm}×{h_mm} mm ไม่ผ่านเกณฑ์")
                c1,c2,c3=st.columns(3)
                c1.metric("Moment Util.",f"{r['util_M']}%",f"φMn={r['pMn']} vs Mu={r['Mu']} kN·m",delta_color="off")
                c2.metric("Shear Util.",f"{r['util_V']}%",f"φVc={r['pVc']} kN",delta_color="off")
                c3.metric("Deflection Util.",f"{r['util_D']}%",f"δ={r['dt']} mm (limit {r['l240']} mm)",delta_color="off")
                st.subheader("Utilization")
                util_bar("Moment",r["util_M"])
                util_bar("Shear",r["util_V"])
                util_bar("Deflection",r["util_D"])
                st.info(f"⚡ รับ Total Load ได้สูงสุด **{r['w_max']} kN/m** (ใช้จริง {wdl+wll} kN/m)")
                st.subheader("💡 Section ที่ประหยัดกว่าและยังผ่านเกณฑ์")
                opts=[]
                for cb in range(150,b_mm+50,50):
                    for ch in range(300,h_mm+50,50):
                        if cb*ch<b_mm*h_mm:
                            cr=beam_design(cb,ch,span,wdl,wll,fc,fy,cover,bar_dia)
                            if cr and cr["_ok"]:
                                opts.append({"Section":cr["Section"],
                                             "คอนกรีต(m³)":cr["คอนกรีต(m³)"],
                                             "ประหยัด(%)":round((1-cr["_vol"]/r["vol"])*100,1),
                                             "As(mm²)":cr["As(mm²)"],"Overall":cr["Overall"]})
                if opts:
                    odf=pd.DataFrame(opts).sort_values("ประหยัด(%)",ascending=False)
                    best=odf.iloc[0]
                    st.success(f"✅ ลดเป็น **{best['Section']} mm** ประหยัด **{best['ประหยัด(%)']}%**")
                    st.dataframe(odf,use_container_width=True,hide_index=True)
                else: st.info("ไม่พบ section ที่เล็กกว่า — optimal แล้ว")
            else: st.info("👈 ใส่ข้อมูลแบบที่มีอยู่แล้วกด ตรวจสอบ")


# ██████████████████████████████████████████████████████████████
# TAB 2: เสา
# ██████████████████████████████████████████████████████████████
with tab_col:
    st.markdown("### 🏛️ วิเคราะห์เสา RC — Short Column (Axial + Uniaxial Moment)")
    mode_c = st.radio("โหมด",["🔧 Design — หา As ที่ต้องการ",
                               "🔍 Check — ตรวจสอบแบบที่มีอยู่"],
                      horizontal=True,key="mode_col")
    st.divider()

    def col_capacity(b_mm,h_mm,rho_g,fc,fy):
        Ag  = b_mm*h_mm                          # mm²
        Ast = rho_g*Ag
        # ACI 318: φPn_max (tied) = 0.80φ[0.85f'c(Ag-Ast)+Ast·fy]
        phi = 0.65
        Pn0 = 0.85*fc*(Ag-Ast)+Ast*fy           # N (ใช้ MPa·mm²)
        phiPn_max = phi*0.80*Pn0/1000            # kN
        # Pure moment (φMn ที่ P=0 — ประมาณ)
        cover=40; bar_d=20
        d = h_mm - cover - bar_d/2
        As_tension = (rho_g/2)*Ag
        a = As_tension*fy/(0.85*fc*b_mm)
        phiMn = 0.9*As_tension*fy*(d-a/2)/1e6   # kN·m
        return phiPn_max, phiMn, Ag, Ast

    def col_check(b_mm,h_mm,n_bars,bar_mm,col_h,Pu,Mu,fc,fy,cover_mm):
        Ag  = b_mm*h_mm
        As  = n_bars*np.pi*(bar_mm/2)**2
        rho = As/Ag
        phi = 0.65
        Pn0 = 0.85*fc*(Ag-As)+As*fy
        phiPn = phi*0.80*Pn0/1000                # kN
        d     = h_mm-cover_mm-(bar_mm/2)
        a     = (As/2)*fy/(0.85*fc*b_mm)
        phiMn = 0.9*(As/2)*fy*(d-a/2)/1e6        # kN·m
        # Slenderness: kL/r (k=1.0 pin-pin, r=0.3h สำหรับ rect.)
        r   = 0.3*h_mm
        kLr = (1.0*col_h*1000)/r
        slim = "Short (OK)" if kLr<=34 else "Slender — ต้องวิเคราะห์เพิ่ม"
        # Interaction: P/φPn + M/φMn ≤ 1 (simplified)
        interact = round(Pu/phiPn + Mu/phiMn,3) if phiMn>0 else 999
        util_P = round(Pu/phiPn*100,1)
        util_M = round(Mu/phiMn*100,1) if phiMn>0 else 999
        return {"phiPn":round(phiPn,2),"phiMn":round(phiMn,2),
                "rho_g":round(rho*100,2),"kLr":round(kLr,1),
                "slender":slim,"interact":interact,
                "util_P":util_P,"util_M":util_M,
                "ok":interact<=1.0 and rho>=0.01 and rho<=0.08}

    if mode_c.startswith("🔧"):
        col_in,col_out=st.columns([1,3])
        with col_in:
            st.subheader("พารามิเตอร์")
            b_mm=st.number_input("กว้าง b (mm)",150,1500,400,50,key="cdb")
            h_mm=st.number_input("สูง h (mm)",150,1500,400,50,key="cdh")
            col_h=st.number_input("ความสูงเสา (m)",1.0,20.0,3.5,0.5,key="cdH")
            Pu=st.number_input("Pu — แรงอัด (kN)",0.0,50000.0,1000.0,50.0,key="cdPu")
            Mu=st.number_input("Mu — โมเมนต์ (kN·m)",0.0,5000.0,50.0,10.0,key="cdMu")
            fc=st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="cdfc")
            fy=st.selectbox("fy",[250,390,500],index=1,key="cdfy",format_func=lambda x:f"SD{x}")
            go=st.button("คำนวณ",type="primary",use_container_width=True,key="cdgo")

        with col_out:
            if go:
                # หา rho ที่ต้องการ
                Ag=b_mm*h_mm; phi=0.65
                # จาก φPn_max >= Pu: หา Ast
                # Pu <= 0.80φ[0.85f'c(Ag-Ast)+Ast·fy]
                # Pu/(0.80φ) = 0.85f'c·Ag - 0.85f'c·Ast + fy·Ast
                # Ast(fy-0.85f'c) = Pu/(0.80φ) - 0.85f'c·Ag
                target = Pu*1000/(0.80*phi)  # N
                num    = target - 0.85*fc*Ag
                denom  = fy - 0.85*fc
                Ast_req= max(num/denom, 0.01*Ag)
                rho_req= Ast_req/Ag

                r=col_check(b_mm,h_mm,
                            n_bars=max(4,int(Ast_req/(np.pi*(20/2)**2))+1),
                            bar_mm=20,col_h=col_h,Pu=Pu,Mu=Mu,fc=fc,fy=fy,cover_mm=40)

                st.subheader(f"ผล: เสา {b_mm}×{h_mm} mm")
                c1,c2,c3=st.columns(3)
                c1.metric("As ที่ต้องการ",f"{Ast_req:.0f} mm²",f"ρg={rho_req*100:.2f}%")
                c2.metric("φPn สูงสุด",f"{r['phiPn']} kN",f"Pu={Pu} kN")
                c3.metric("kL/r",f"{r['kLr']}",r["slender"])

                st.subheader("Utilization")
                util_bar("Axial (P/φPn)",r["util_P"])
                util_bar("Moment (M/φMn)",r["util_M"])

                interact_ok = r["interact"]<=1.0
                if interact_ok:
                    st.success(f"✅ Interaction ratio = {r['interact']} ≤ 1.0 — ผ่าน")
                else:
                    st.error(f"❌ Interaction ratio = {r['interact']} > 1.0 — ไม่ผ่าน เพิ่ม section หรือเหล็ก")

                if rho_req<0.01: st.warning("⚠️ ใช้ ρg min = 1% ตาม ACI 318")
                if rho_req>0.08: st.error("❌ ρg เกิน 8% — เพิ่มขนาด section")

                # เสนอ section ทางเลือก
                st.subheader("📊 เปรียบเทียบขนาด section เสา")
                rows=[]
                for b in range(250,max(b_mm+150,751),50):
                    for h in [b]:   # เสาสี่เหลี่ยมจัตุรัส
                        Ag_=b*h; phi_=0.65
                        num_=Pu*1000/(0.80*phi_)-0.85*fc*Ag_
                        den_=fy-0.85*fc
                        Ast_=max(num_/den_,0.01*Ag_)
                        rho_=Ast_/Ag_
                        r2=col_check(b,h,max(4,int(Ast_/(np.pi*100))+1),20,col_h,Pu,Mu,fc,fy,40)
                        rows.append({"Section":f"{b}×{h}",
                                     "As ต้องการ(mm²)":round(Ast_,0),
                                     "ρg(%)":round(rho_*100,2),
                                     "φPn(kN)":r2["phiPn"],
                                     "Interaction":r2["interact"],
                                     "kL/r":r2["kLr"],
                                     "คอนกรีต(m³)":round(b*h/1e6*col_h,4),
                                     "Overall":"✅" if r2["ok"] and r2["interact"]<=1 else "❌"})
                df=pd.DataFrame(rows)
                st.dataframe(df,use_container_width=True,hide_index=True)
                st.download_button("⬇️ CSV",df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                                   "column_design.csv","text/csv",use_container_width=True)
            else: st.info("👈 ใส่ค่าแล้วกด คำนวณ")

    else:
        col_in,col_out=st.columns([1,3])
        with col_in:
            st.subheader("แบบเสาที่มีอยู่")
            b_mm=st.number_input("กว้าง b (mm)",150,1500,400,50,key="ckb_c")
            h_mm=st.number_input("สูง h (mm)",150,1500,400,50,key="ckh_c")
            col_h=st.number_input("ความสูงเสา (m)",1.0,20.0,3.5,0.5,key="ckH_c")
            n_bars=st.number_input("จำนวนเหล็ก (เส้น)",4,32,8,2,key="ckn_c")
            bar_dia=st.selectbox("ขนาด DB",[12,16,20,25,28,32],index=3,key="ckdb_c")
            cover=st.number_input("Cover (mm)",20,75,40,5,key="ckcv_c")
            Pu=st.number_input("Pu (kN)",0.0,50000.0,1000.0,50.0,key="ckPu")
            Mu=st.number_input("Mu (kN·m)",0.0,5000.0,50.0,10.0,key="ckMu")
            fc=st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="ckfc_c")
            fy=st.selectbox("fy",[250,390,500],index=1,key="ckfy_c",format_func=lambda x:f"SD{x}")
            go=st.button("ตรวจสอบ",type="primary",use_container_width=True,key="ckgo_c")

        with col_out:
            if go:
                r=col_check(b_mm,h_mm,n_bars,bar_dia,col_h,Pu,Mu,fc,fy,cover)
                if r["ok"] and r["interact"]<=1.0:
                    st.success(f"✅ เสา {b_mm}×{h_mm} mm | {n_bars}-DB{bar_dia} ผ่านทุกเกณฑ์")
                else:
                    st.error(f"❌ เสา {b_mm}×{h_mm} mm ไม่ผ่านเกณฑ์")

                c1,c2,c3,c4=st.columns(4)
                c1.metric("φPn",f"{r['phiPn']} kN",f"Pu={Pu} kN",delta_color="off")
                c2.metric("φMn",f"{r['phiMn']} kN·m",f"Mu={Mu} kN·m",delta_color="off")
                c3.metric("Interaction",r["interact"],"≤1.0 = OK",delta_color="off")
                c4.metric("kL/r",r["kLr"],r["slender"],delta_color="off")

                st.subheader("Utilization")
                util_bar("Axial",r["util_P"])
                util_bar("Moment",r["util_M"])
                st.text(f"   ρg = {r['rho_g']}% (ACI ต้องการ 1–8%)")

                if r["interact"]<=1.0 and (r["util_P"]<70 or r["util_M"]<70):
                    st.subheader("💡 Section ที่เล็กกว่า")
                    opts=[]
                    for b in range(250,b_mm,50):
                        r2=col_check(b,b,n_bars,bar_dia,col_h,Pu,Mu,fc,fy,cover)
                        if r2["ok"] and r2["interact"]<=1.0:
                            opts.append({"Section":f"{b}×{b}",
                                         "rho_g(%)":r2["rho_g"],
                                         "Interaction":r2["interact"],
                                         "คอนกรีต(m³)":round(b*b/1e6*col_h,4),
                                         "ประหยัด(%)":round((1-b*b/(b_mm*h_mm))*100,1)})
                    if opts:
                        odf=pd.DataFrame(opts)
                        best=odf.iloc[-1]
                        st.success(f"✅ ลดได้เป็น **{best['Section']} mm** ประหยัด {best['ประหยัด(%)']}%")
                        st.dataframe(odf,use_container_width=True,hide_index=True)
            else: st.info("👈 ใส่ข้อมูลแบบที่มีอยู่แล้วกด ตรวจสอบ")


# ██████████████████████████████████████████████████████████████
# TAB 3: พื้น (One-way Slab)
# ██████████████████████████████████████████████████████████████
with tab_slab:
    st.markdown("### ⬜ วิเคราะห์พื้น RC — One-Way Slab")
    mode_s=st.radio("โหมด",["🔧 Design — หาความหนาและเหล็กที่เหมาะสม",
                             "🔍 Check — ตรวจสอบแบบที่มีอยู่"],
                    horizontal=True,key="mode_slab")
    st.caption("วิเคราะห์ต่อแถบกว้าง 1 เมตร")
    st.divider()

    def slab_min_thick(span,support):
        # ACI 318 Table 7.3.1.1
        table={"Simply Supported":20,"One End Continuous":24,
               "Both Ends Continuous":28,"Cantilever":10}
        return span*1000/table[support]  # mm

    def slab_analyze(t_mm,span,wdl,wll,fc,fy,cover_mm,bar_mm,support):
        b=1000  # mm (1 เมตร)
        h=t_mm
        d=h-cover_mm-bar_mm/2
        w=wdl+wll
        Ec_=Ec(fc)*1e-6  # MPa (kN/m²→MPa: /1000, แล้ว *1000mm²=mm² → ÷1000)
        Ec_mm=Ec(fc)/1000  # kN/mm²... ใช้ kN/m² ต่อ
        # moment coeff
        coeff={"Simply Supported":8,"One End Continuous":10,
               "Both Ends Continuous":12,"Cantilever":2}[support]
        Mu=(wdl*1.2+wll*1.6)*span**2/coeff   # kN·m per m
        Vu=(wdl*1.2+wll*1.6)*span/2           # kN per m

        # Deflection (total w, gross I per m)
        Igm=b*h**3/12   # mm⁴ per m ... แต่ใช้หน่วย m
        I_=1.0*(h/1000)**3/12  # m⁴/m-width
        A_=1.0*(h/1000)
        Ec_v=Ec(fc)
        defl_t=5*w*span**4/(384*Ec_v*I_)*1000
        defl_l=5*wll*span**4/(384*Ec_v*I_)*1000
        l240,l360=span*1000/240,span*1000/360

        # As required
        Rn=(Mu*1e6)/(0.9*b*d**2)  # MPa
        disc=1-(2*Rn)/(0.85*fc)
        if disc<0: return None
        rho=max((0.85*fc/fy)*(1-np.sqrt(disc)), max(0.0018,0.0014))
        As_req=rho*b*d   # mm²/m

        # Spacing of bars
        As_bar=np.pi*(bar_mm/2)**2
        spacing=As_bar/As_req*1000  # mm
        spacing=min(spacing,min(3*h,450))  # ACI max spacing

        # φMn check
        As_use=As_bar/(spacing/1000)
        a_=As_use*fy/(0.85*fc*b)
        pMn=0.9*As_use*fy*(d-a_/2)/1e6

        # φVc (no shear reinf for slab)
        pVc=0.75*0.17*np.sqrt(fc)*b*d/1000

        min_t=slab_min_thick(span,support)
        return {"t(mm)":t_mm,"d(mm)":round(d,1),
                "Mu(kN·m/m)":round(Mu,2),"Vu(kN/m)":round(Vu,2),
                "Defl รวม(mm)":round(defl_t,3),"L/240(mm)":round(l240,2),
                "As ต้องการ(mm²/m)":round(As_req,1),
                "DB แนะนำ":f"DB{bar_mm}@{spacing:.0f}mm",
                "φMn(kN·m/m)":round(pMn,2),"φVc(kN/m)":round(pVc,2),
                "Moment":"✅" if pMn>=Mu else "❌",
                "Shear":"✅" if pVc>=Vu else "⚠️ เพิ่มความหนา",
                "Deflection":"✅" if defl_t<=l240 else "❌",
                "Min.t ACI(mm)":round(min_t,0),
                "ตรวจ Min.t":"✅" if t_mm>=min_t else "❌",
                "Overall":"✅ PASS" if (pMn>=Mu and pVc>=Vu and defl_t<=l240 and t_mm>=min_t) else "❌ FAIL",
                "_ok":(pMn>=Mu and pVc>=Vu and defl_t<=l240 and t_mm>=min_t)}

    if mode_s.startswith("🔧"):
        col_in,col_out=st.columns([1,3])
        with col_in:
            st.subheader("พารามิเตอร์")
            span =st.number_input("Span (m)",1.0,15.0,4.0,0.5,key="ss")
            wdl  =st.number_input("DL (kN/m²)",0.0,50.0,3.0,0.5,key="sdl")
            wll  =st.number_input("LL (kN/m²)",0.0,50.0,3.0,0.5,key="sll")
            fc   =st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="sfc")
            fy   =st.selectbox("fy",[250,390,500],index=1,key="sfy",format_func=lambda x:f"SD{x}")
            sup  =st.selectbox("รูปแบบการรองรับ",
                               ["Simply Supported","One End Continuous",
                                "Both Ends Continuous","Cantilever"],index=2,key="ssup")
            cover=st.number_input("Cover (mm)",15,50,25,5,key="scv")
            bar_d=st.selectbox("DB เหล็กพื้น",[10,12,16,20],index=1,key="sdb")
            st.caption("ความหนาที่เปรียบเทียบ")
            t_min=st.number_input("ต่ำสุด (mm)",50,500,100,25,key="tmin")
            t_max=st.number_input("สูงสุด (mm)",100,600,300,25,key="tmax")
            go=st.button("วิเคราะห์",type="primary",use_container_width=True,key="sgo")

        with col_out:
            if go:
                min_t=slab_min_thick(span,sup)
                st.info(f"📐 ความหนาขั้นต่ำ ACI 318 ({sup}): **{min_t:.0f} mm**")
                res=[]
                for t in range(int(t_min),int(t_max)+25,25):
                    r=slab_analyze(t,span,wdl,wll,fc,fy,cover,bar_d,sup)
                    if r: res.append(r)
                if not res: st.error("ไม่มีข้อมูล"); st.stop()
                df=pd.DataFrame(res)
                passed=df[df["_ok"]]
                if not passed.empty:
                    best=passed.iloc[0]
                    st.success(f"✅ ความหนาต่ำสุดที่ผ่านเกณฑ์: **{best['t(mm)']} mm** | {best['DB แนะนำ']} | As={best['As ต้องการ(mm²/m)']} mm²/m")
                else: st.error("ไม่มีความหนาใดผ่าน — ลองเพิ่มช่วง")
                disp=[c for c in df.columns if not c.startswith("_")]
                st.dataframe(df[disp],use_container_width=True,hide_index=True)
                st.download_button("⬇️ CSV",df[disp].to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                                   "slab_design.csv","text/csv",use_container_width=True)
            else: st.info("👈 ใส่ค่าแล้วกด วิเคราะห์")

    else:
        col_in,col_out=st.columns([1,3])
        with col_in:
            st.subheader("แบบพื้นที่มีอยู่")
            t_mm =st.number_input("ความหนาพื้น (mm)",50,600,200,25,key="ckt")
            span =st.number_input("Span (m)",1.0,15.0,4.0,0.5,key="cks_s")
            bar_d=st.selectbox("DB เหล็กพื้น",[10,12,16,20],index=1,key="ckdb_s")
            spac =st.number_input("ระยะเหล็ก Spacing (mm)",50,450,150,25,key="cksp")
            cover=st.number_input("Cover (mm)",15,50,25,5,key="ckcv_s")
            wdl  =st.number_input("DL (kN/m²)",0.0,50.0,3.0,0.5,key="ckdl_s")
            wll  =st.number_input("LL (kN/m²)",0.0,50.0,3.0,0.5,key="ckll_s")
            fc   =st.number_input("f'c (MPa)",15.0,70.0,28.0,2.0,key="ckfc_s")
            fy   =st.selectbox("fy",[250,390,500],index=1,key="ckfy_s",format_func=lambda x:f"SD{x}")
            sup  =st.selectbox("รูปแบบการรองรับ",
                               ["Simply Supported","One End Continuous",
                                "Both Ends Continuous","Cantilever"],index=2,key="cksup_s")
            go=st.button("ตรวจสอบ",type="primary",use_container_width=True,key="ckgo_s")

        with col_out:
            if go:
                r=slab_analyze(t_mm,span,wdl,wll,fc,fy,cover,bar_d,sup)
                if not r: st.error("ข้อมูลไม่ถูกต้อง"); st.stop()
                As_prov=np.pi*(bar_d/2)**2/(spac/1000)
                if r["_ok"]:
                    st.success(f"✅ พื้นหนา {t_mm} mm | DB{bar_d}@{spac} ผ่านทุกเกณฑ์")
                else:
                    st.error(f"❌ พื้นหนา {t_mm} mm ไม่ผ่านเกณฑ์")

                c1,c2,c3,c4=st.columns(4)
                c1.metric("Moment","✅" if r["Moment"]=="✅" else "❌",
                           f"φMn={r['φMn(kN·m/m)']} vs Mu={r['Mu(kN·m/m)']}",delta_color="off")
                c2.metric("Shear",r["Shear"],f"φVc={r['φVc(kN/m)']} kN/m",delta_color="off")
                c3.metric("Deflection",r["Deflection"],
                           f"δ={r['Defl รวม(mm)']} (limit {r['L/240(mm)']})",delta_color="off")
                c4.metric("Min. Thickness",r["ตรวจ Min.t"],
                           f"{t_mm} mm (ACI min {r['Min.t ACI(mm)']} mm)",delta_color="off")

                st.subheader("Utilization")
                util_bar("Moment",r["Mu(kN·m/m)"]/r["φMn(kN·m/m)"]*100 if r["φMn(kN·m/m)"]>0 else 0)
                util_bar("Deflection",r["Defl รวม(mm)"]/r["L/240(mm)"]*100 if r["L/240(mm)"]>0 else 0)

                if As_prov < r["As ต้องการ(mm²/m)"]:
                    st.warning(f"⚠️ As ที่ให้ {As_prov:.0f} mm²/m < As ต้องการ {r['As ต้องการ(mm²/m)']} mm²/m — ลด spacing")
                else:
                    st.success(f"✅ As ที่ให้ {As_prov:.0f} mm²/m ≥ As ต้องการ {r['As ต้องการ(mm²/m)']} mm²/m")

                st.subheader("💡 ความหนาต่ำสุดที่ประหยัดกว่า")
                opts=[]
                for t in range(100,t_mm,25):
                    r2=slab_analyze(t,span,wdl,wll,fc,fy,cover,bar_d,sup)
                    if r2 and r2["_ok"]:
                        opts.append({"ความหนา(mm)":t,"As(mm²/m)":r2["As ต้องการ(mm²/m)"],
                                     "DB แนะนำ":r2["DB แนะนำ"],
                                     "ประหยัด(%)":round((1-t/t_mm)*100,1),"Overall":r2["Overall"]})
                if opts:
                    odf=pd.DataFrame(opts)
                    best=odf.iloc[0]
                    st.success(f"✅ ลดความหนาเป็น **{best['ความหนา(mm)']} mm** ประหยัด {best['ประหยัด(%)']}%")
                    st.dataframe(odf,use_container_width=True,hide_index=True)
                else: st.info("ความหนานี้ประหยัดที่สุดแล้ว")
            else: st.info("👈 ใส่ข้อมูลแบบที่มีอยู่แล้วกด ตรวจสอบ")
