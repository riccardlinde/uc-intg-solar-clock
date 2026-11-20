import base64,io,json,math,random,ssl,time,urllib.request
from datetime import datetime,timedelta
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
_wc={"ts":0,"t":"","temp":"","sr":7.75,"ss":17.5,"wmo":0}
def _solar(lat=41.39,lon=2.16,unit="C"):
 if time.time()-_wc.get("ts",0)<900 and _wc.get("temp"):return _wc
 try:
  host=".".join(["api","open-meteo","com"])
  u="https:/"+"/"+host+"/v1/forecast?latitude=41.3874&longitude=2.1686&current_weather=true&daily=sunrise,sunset&timezone=Europe%2FMadrid"
  d=json.loads(urllib.request.urlopen(u,timeout=8,context=ssl._create_unverified_context()).read().decode())
  cw=d.get("current_weather",{});dl=d.get("daily",{})
  sr=datetime.fromisoformat(next(iter(dl.get("sunrise"))));ss=datetime.fromisoformat(next(iter(dl.get("sunset"))))
  _wc.update({"sr":sr.hour+sr.minute/60.0,"ss":ss.hour+ss.minute/60.0,"wmo":int(cw.get("weathercode",0)),"temp":f"{round(cw.get('temperature',0))}","ts":time.time()})
 except Exception as ex:print("OM ERR:",ex)
 return _wc
def _f(sz):
 for p in("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Black.ttf","/usr/share/fonts/truetype/roboto/Roboto-Black.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
  try:return ImageFont.truetype(p,sz)
  except Exception:pass
 return ImageFont.load_default()
def _sun_glow(rad):
 sz=rad*2;g=Image.new("RGBA",(sz,sz),(0,0,0,0));px=g.load()
 for y in range(sz):
  for x in range(sz):
   d=math.hypot(x-rad,y-rad)/float(rad)
   if d<1.0:
    a=int(225*((1.0-d)**2.3));px[x,y]=(255,250,230,a)
 return g
_SG=_sun_glow(54)
def render_analog_clock_base64(now,theme="dark",show_date=True,time_format="24h",temp_unit="C",show_moon=True,show_temp=True,show_sun_events=True,latitude=41.39,longitude=2.16,mock_wmo=None,**kw):
 w,h,wh=360,360,360;sc=_solar(latitude,longitude,temp_unit);sc=dict(sc,wmo=mock_wmo) if mock_wmo is not None else sc
 hr=now.hour+now.minute/60.0;sr,ss,wmo=sc["sr"],sc["ss"],sc["wmo"]
 cy=wh//2;cx=w//2;orb_r=115;sa=math.radians(hr*15+90);sx,sy=cx+orb_r*math.cos(sa),cy+orb_r*math.sin(sa)
 day_f=max(0.0,min(1.0,math.sin(math.pi*(hr-sr)/(ss-sr)))) if sr<=hr<=ss else 0.0
 twi=max(0.0,1.0-min(abs(hr-sr),abs(hr-ss))/1.5);sun_vis=1.0 if sr<=hr<=ss else max(0.0,1.0-min((hr-ss)%24.0,(sr-hr)%24.0)/0.75)
 is_rain=wmo>=51;is_cloud=wmo in(2,3,45,48) or is_rain
 img=Image.new("RGB",(w,h),(10,16,38));px=img.load()
 sr_ang=(sr*15.0+90.0)%360.0;ss_ang=(ss*15.0+90.0)%360.0
 day_span=(ss_ang-sr_ang)%360.0
 decl=math.radians(23.44*math.sin(2.0*math.pi*(now.timetuple().tm_yday-81)/365.0))
 spd_f=1.0/max(0.75,math.sqrt(max(0.15,1.0-(math.sin(decl)/math.cos(math.radians(41.39)))**2)))
 civ_deg=7.5*spd_f;naut_deg=15.0*spd_f;ast_deg=22.5*spd_f
 hrs_dark=0.0 if sr<=hr<=ss else min((hr-ss)%24.0,(sr-hr)%24.0)
 night_deep=min(1.0,hrs_dark/3.5);n_dim=1.0-0.72*night_deep
 for y in range(wh):
  for x in range(w):
   ang=(math.degrees(math.atan2(y-cy,x-cx)))%360.0
   rel=(ang-sr_ang)%360.0
   dist_edge=min(rel,day_span-rel) if rel<=day_span else -min((sr_ang-ang)%360.0,(ang-ss_ang)%360.0)
   sp=max(0.0,1.0-math.hypot(x-sx,y-sy)/230.0)*max(day_f,twi*0.75)
   if dist_edge>=0:
    gold_f=math.exp(-dist_edge/(civ_deg*2.2))
    zen_f=1.0-gold_f
    b_boost=(0.14+0.31*n_dim)+0.55*max(day_f,twi*0.65)
    if is_rain:
     r=int((36+52*gold_f)*b_boost+58*twi*gold_f)
     g=int((48+66*gold_f)*b_boost+38*twi*gold_f)
     b=int((78+92*gold_f)*b_boost+24*twi*gold_f)
    else:
     r=int((62*zen_f+196*gold_f)*b_boost+185*twi*gold_f+72*sp)
     g=int((136*zen_f+224*gold_f)*b_boost+118*twi*gold_f+68*sp)
     b=int((234*zen_f+252*gold_f)*b_boost+42*twi*gold_f+44*sp)
    px[x,y]=(min(255,r),min(255,g),min(255,b))
   else:
    d_out=-dist_edge;rad_c=max(0.0,min(1.0,1.0-math.hypot(x-cx,y-cy)/215.0))
    civ_f=max(0.0,1.0-d_out/civ_deg)
    naut_f=math.exp(-max(0.0,d_out-civ_deg*0.5)/naut_deg)
    ast_f=math.exp(-d_out/(ast_deg*1.45))
    r=int((8+14*rad_c+28*ast_f+40*naut_f+72*civ_f)*n_dim+36*twi*naut_f)
    g=int((13+24*rad_c+44*ast_f+56*naut_f+62*civ_f)*n_dim+32*twi*naut_f)
    b=int((30+44*rad_c+76*ast_f+86*naut_f+70*civ_f)*n_dim+44*twi*naut_f)
    px[x,y]=(min(255,r),min(255,g),min(255,b))
 if is_cloud:
  cl=Image.new("RGBA",(w,wh),(0,0,0,0));cd=ImageDraw.Draw(cl)
  if is_rain:
   for y2 in range(0,115):
    a=int(185*((1.0-y2/115.0)**1.6))
    cd.line([(0,y2),(w,y2)],fill=(36,44,62,a))
   for cx2,cy2,rw,rh in((75,4,85,34),(175,-4,98,38),(275,6,85,34),(125,22,70,24),(225,20,74,24)):
    cd.ellipse([cx2-rw,cy2-rh,cx2+rw,cy2+rh],fill=(58,68,88,165))
   cl=cl.filter(ImageFilter.GaussianBlur(11))
   rl=Image.new("RGBA",(w,wh),(0,0,0,0));rd=ImageDraw.Draw(rl)
   rng=random.Random(int(hr*10));ra=int(55+35*day_f)
   for _ in range(42):
    rx2=rng.randint(28,w-28);ry2=rng.randint(28,cy-14)
    rd.line([(rx2,ry2),(rx2-4,ry2+15)],fill=(195,220,250,ra),width=1)
   img.paste(cl,(0,0),cl);img.paste(rl,(0,0),rl)
  else:
   puffs=[(85,6,56,28),(132,-4,52,32),(182,4,60,28),(235,-2,54,30),(282,8,52,26),(155,18,46,20),(212,16,48,20)]
   for cx2,cy2,rw,rh in puffs:
    cd.ellipse([cx2-rw,cy2-rh,cx2+rw,cy2+rh],fill=(255,255,255,int(65+115*max(day_f,twi*0.55))))
   cl=cl.filter(ImageFilter.GaussianBlur(13));img.paste(cl,(0,0),cl)
 d=ImageDraw.Draw(img)
 if day_f<0.22 and not is_cloud:
  for sx2,sy2 in((46,40),(92,28),(278,36),(314,58),(64,252),(112,278),(266,258),(304,232),(222,34),(135,268)):
   d.ellipse([sx2-1,sy2-1,sx2+1,sy2+1],fill=(210,224,248))
 rx,ry=cx-10,cy+2
 def rp(a,ins=0):
  ca,sa=math.cos(a),math.sin(a);t=min((rx-ins)/abs(ca) if abs(ca)>1e-6 else 1e9,(ry-ins)/abs(sa) if abs(sa)>1e-6 else 1e9);return cx+t*ca,cy+t*sa
 for i in range(60):
  a=math.radians(i*6-90);d.line([rp(a,0),rp(a,14 if i%5==0 else 8)],fill=(255,255,255) if i%5==0 else (235,240,248),width=3 if i%5==0 else 2)
 def draw_arc_txt(txt,ang_deg,rad_t,flip=False,bright=True,f_sz=15,step=6.2,alpha_m=1.0):
  af=_f(f_sz);tot=step*(len(txt)-1);s_ang=ang_deg+(tot/2 if flip else -tot/2)
  col=(255,255,255,int(250*alpha_m)) if bright else (225,235,250,int(145*alpha_m))
  for idx,ch in enumerate(txt):
   a_deg=s_ang+(-idx*step if flip else idx*step);a_rad=math.radians(a_deg)
   tx,ty=cx+rad_t*math.cos(a_rad),cy+rad_t*math.sin(a_rad)
   ci=Image.new("RGBA",(48,48),(0,0,0,0));cd=ImageDraw.Draw(ci);bx0,by0,bx1,by1=cd.textbbox((0,0),ch,font=af);cd.text((24-(bx0+bx1)/2.0,24-(by0+by1)/2.0),ch,fill=col,font=af)
   rot=ci.rotate(-(a_deg-90) if flip else -(a_deg+90),resample=Image.BICUBIC)
   img.paste(rot,(int(round(tx-24)),int(round(ty-24))),rot)
 sr_h,sr_m=int(sr),int(round((sr%1)*60));ss_h,ss_m=int(ss),int(round((ss%1)*60));sa_deg=hr*15+90;bot_half=0<(sa_deg%360)<180
 is_day=sr<=hr<ss;a_sr,a_ss=sa_deg-30,sa_deg+30
 gf_big=_f(142);nl=Image.new("RGBA",(w,wh),(0,0,0,0));nd=ImageDraw.Draw(nl)
 nd.text((26,48),"1",fill=(255,255,255,255),font=gf_big,anchor="mm");nd.text((74,48),"0",fill=(255,255,255,255),font=gf_big,anchor="mm")
 for num,nx,ny in(("2",w-44,48),("4",w-26,wh-38),("8",36,wh-38)):
  nd.text((nx,ny),num,fill=(255,255,255,255),font=gf_big,anchor="mm")
 mk=Image.new("L",(w,wh),255);md2=ImageDraw.Draw(mk);md2.ellipse([cx-163,cy-163,cx+163,cy+163],fill=0)
 nl.putalpha(Image.composite(nl.getchannel("A"),Image.new("L",(w,wh),0),mk))
 mstr=now.strftime("%M");ma=math.radians(now.minute*6-90);tf_m=_f(52);_,by0_m,_,by1_m=d.textbbox((0,0),"0",font=tf_m);h_ink=by1_m-by0_m;r_m=orb_r+h_ink/2.0+5.0;top_h=math.sin(ma)<0;sgn=1.0 if top_h else -1.0;ws_m=[tf_m.getlength(c) for c in mstr];gap_m=-5.0;angs=[(w_c+gap_m)/r_m for w_c in ws_m];cur_a=ma-sgn*(sum(angs)-gap_m/r_m)/2.0
 for idx_m,(ch,w_c,da) in enumerate(zip(mstr,ws_m,angs)):
  r_adj=r_m+(1.8 if idx_m==0 else 1.0);ca=cur_a+sgn*(w_c/2.0)/r_m;rot=-(math.degrees(ca)+90) if top_h else -(math.degrees(ca)-90);ci=Image.new("RGBA",(110,110),(0,0,0,0));ImageDraw.Draw(ci).text((55,55-(by0_m+by1_m)/2.0),ch,fill=((255,255,255,255) if is_day else (215,224,240,145)),font=tf_m,anchor="ma");ci=ci.rotate(rot,resample=Image.Resampling.BICUBIC,expand=True);img.paste(ci,(int(round(cx+r_adj*math.cos(ca)-ci.width/2.0)),int(round(cy+r_adj*math.sin(ca)-ci.height/2.0))),ci);cur_a+=sgn*da
 sg2=Image.new("RGBA",(136,136),(0,0,0,0));sgp=sg2.load()
 for yy in range(136):
  for xx in range(136):
   dd=math.hypot(xx-68,yy-68)/68.0
   if dd<1.0:sgp[xx,yy]=(255,246,205,int(145*((1.0-dd)**2.2)))
 img.paste(sg2,(int(sx-68),int(sy-68)),sg2);rm_s=Image.new("L",(160,160),0);rd_s=ImageDraw.Draw(rm_s)
 for k in range(12):
  ra_s=k*math.pi/6.0;r_out=62 if k%2==0 else 48;w_a=0.14 if k%2==0 else 0.10
  pts=[(80+18*math.cos(ra_s-w_a),80+18*math.sin(ra_s-w_a)),(80+r_out*math.cos(ra_s),80+r_out*math.sin(ra_s)),(80+18*math.cos(ra_s+w_a),80+18*math.sin(ra_s+w_a))]
  rd_s.polygon(pts,fill=255 if k%2==0 else 190)
 rb=ImageChops.add(rm_s.filter(ImageFilter.GaussianBlur(4.5)).point(lambda v:int(v*0.85)),rm_s.filter(ImageFilter.GaussianBlur(9.5)).point(lambda v:int(v*0.75)));rbp=rb.load()
 for yy in range(160):
  for xx in range(160):
   dd=min(1.0,math.hypot(xx-80,yy-80)/78.0);rbp[xx,yy]=int(rbp[xx,yy]*((1.0-dd)**1.5))
 rl_s=Image.new("RGBA",(160,160),(255,249,222,0));rl_s.putalpha(rb);img.paste(rl_s,(int(sx-80),int(sy-80)),rl_s);img.paste(_SG,(int(sx-54),int(sy-54)),_SG);img.paste(nl,(0,0),nl);d=ImageDraw.Draw(img)
 ph=((time.time()-947182440)/86400.0)%29.53058867/29.53058867;ma2=sa-ph*2*math.pi;mx2,my2=cx+orb_r*math.cos(ma2),cy+orb_r*math.sin(ma2)
 srx0,sry0=cx+(orb_r-14)*math.cos(math.radians(a_sr)),cy+(orb_r-14)*math.sin(math.radians(a_sr));ssx0,ssy0=cx+(orb_r-14)*math.cos(math.radians(a_ss)),cy+(orb_r-14)*math.sin(math.radians(a_ss));rem_h=(ss-hr) if sr<=hr<ss else ((sr-hr)%24.0);rm_tot=max(1,int(round(rem_h*60)));cd_txt=f"{rm_tot//60}h{rm_tot%60:02d}" if rm_tot>=60 else f"{rm_tot}m";a_cd=(sa_deg-(15.5+(len(cd_txt)-1)*3.1))%360.0;hrs_since=(hr-sr)%24.0 if is_day else (hr-ss)%24.0;tot_h=max(0.25,(ss-sr)%24.0 if is_day else (sr-ss)%24.0);prog=max(0.0,min(1.0,hrs_since/tot_h));tail_deg=15.5+(len(cd_txt)-1)*6.2+3.0;fade_in=max(0.0,min(1.0,(hrs_since*15.0-tail_deg)/12.0));fade_out=max(0.0,min(1.0,(rem_h*15.0-3.0)/15.0));cd_vis=(0.38+0.62*max(0.0,min(1.0,(prog-0.50)/0.25)))*fade_in*fade_out;sdist=math.hypot(sx-mx2,sy-my2);mdist=min(math.hypot(srx0-mx2,sry0-my2),math.hypot(ssx0-mx2,ssy0-my2),math.hypot(cx+orb_r*math.cos(math.radians(a_cd))-mx2,cy+orb_r*math.sin(math.radians(a_cd))-my2));mfade=max(0.12,min(1.0,(mdist-14.0)/28.0));ecl=max(0.0,1.0-sdist/38.0)*(1.0 if sun_vis>0.2 else 0.0)
 ml=Image.new("RGBA",(96,96),(0,0,0,0));mpx=ml.load();lm=Image.new("L",(96,96),0);lpx=lm.load();mr=17
 for yy in range(96):
  for xx in range(96):
   dx,dy=xx-48,yy-48
   if dx*dx+dy*dy<=mr*mr:
    xm=math.sqrt(max(0,mr*mr-dy*dy));lit=(dx>=-xm*math.cos(ph*2*math.pi)) if ph<0.5 else (dx<=xm*math.cos((1.0-ph)*2*math.pi))
    mpx[xx,yy]=(242,247,255,int(252*mfade)) if lit else (0,0,0,int((185 if ecl>0.05 else 255)*mfade))
    if lit:lpx[xx,yy]=int(235*mfade)
 mg_a=ImageChops.add(lm.filter(ImageFilter.GaussianBlur(6)).point(lambda v:min(255,int(v*1.15))),lm.filter(ImageFilter.GaussianBlur(13)).point(lambda v:min(255,int(v*0.85))))
 mg_col=(255,185,150,0) if abs(ph-0.5)<0.015 else (220,236,255,0);mg=Image.new("RGBA",(96,96),mg_col);mg.putalpha(mg_a)
 if ecl>0.05:ImageDraw.Draw(ml).ellipse([48-mr,48-mr,48+mr,48+mr],outline=(255,246,215,int(210*ecl)),width=2)
 if show_moon:img.paste(mg,(int(mx2-48),int(my2-48)),mg);img.paste(ml,(int(mx2-48),int(my2-48)),ml);d=ImageDraw.Draw(img)
 
 d.ellipse([sx-20,sy-20,sx+20,sy+20],fill=(255,252,238))
 t_sun=((sc.get("temp") or "").replace("°","")) if show_temp else ""
 tf_s=next((ImageFont.truetype(fp,21) for fp in("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf","/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf") if __import__("os").path.exists(fp)),_f(21))
 gap=-1.5 if len(t_sun)>1 else 0.0
 ti=Image.new("L",(80,80),0);td=ImageDraw.Draw(ti);px_t=10.0
 for ch in t_sun:td.text((px_t,10),ch,fill=255,font=tf_s);px_t+=tf_s.getlength(ch)+gap
 bb=ti.getbbox()
 if bb:bx0,by0,bx1,by1=bb;img.paste((0,0,0),(int(round(sx-(bx0+bx1)/2.0)),int(round(sy-(by0+by1)/2.0))),ti)
 if show_sun_events and cd_vis>0.03:draw_arc_txt(cd_txt,a_cd,orb_r,flip=0<a_cd<180,bright=True,f_sz=15,step=6.2,alpha_m=cd_vis)
 for ang_h,hh_s,mm_s,br_h in (() if not show_sun_events else((sr_ang,f"{sr_h:02d}",f"{sr_m:02d}",not is_day),(ss_ang,f"{ss_h:02d}",f"{ss_m:02d}",is_day))):
  if not br_h:continue
  ad=(ang_h%360.0);
  if (sun_vis>0.1 and abs((ad-sa_deg+180.0)%360.0-180.0)<17.0) or abs((ad-a_cd+180.0)%360.0-180.0)<18.0:continue
  ar=math.radians(ad);left_s=90.0<ad<270.0;rot_h=-(ad+180.0) if left_s else -ad;ev_f=max(0.0,min(1.0,(3.5-rem_h)/2.5));col_h=(255,255,255,int(80+170*ev_f));hf_s=_f(15)
  for r_off,txt_p in((orb_r-18,mm_s if left_s else hh_s),(orb_r+18,hh_s if left_s else mm_s)):
   ti_h=Image.new("RGBA",(44,28),(0,0,0,0));ImageDraw.Draw(ti_h).text((22,14),txt_p,fill=col_h,font=hf_s,anchor="mm");ti_h=ti_h.rotate(rot_h,resample=Image.Resampling.BICUBIC,expand=True);img.paste(ti_h,(int(round(cx+r_off*math.cos(ar)-ti_h.width/2.0)),int(round(cy+r_off*math.sin(ar)-ti_h.height/2.0))),ti_h)
 ha,ma=math.radians((now.hour%12+now.minute/60.0)*30-90),math.radians(now.minute*6-90)
 m_rad=orb_r+19;mtx,mty=cx+m_rad*math.cos(ma),cy+m_rad*math.sin(ma)

 rl_orb=Image.new("RGBA",(w,wh),(0,0,0,0));rod=ImageDraw.Draw(rl_orb)
 rod.ellipse([cx-orb_r+1,cy-orb_r+1,cx+orb_r-1,cy+orb_r-1],outline=(205,225,250,235) if day_f>0.2 else (95,115,145,235),width=2)
 omk=Image.new("L",(w,wh),0);omd=ImageDraw.Draw(omk)
 omd.ellipse([sx-21,sy-21,sx+21,sy+21],fill=255);
 if show_moon:omd.ellipse([mx2-19,my2-19,mx2+19,my2+19],fill=255)
 cd_sp=len(cd_txt)*3.1+2.5
 if show_sun_events and cd_vis>0.03:omd.arc([cx-orb_r-5,cy-orb_r-5,cx+orb_r+5,cy+orb_r+5],start=a_cd-cd_sp,end=a_cd+cd_sp,fill=int(255*min(1.0,cd_vis/0.35)),width=14)
 
 rl_orb.putalpha(ImageChops.subtract(rl_orb.getchannel("A"),omk))
 img.paste(rl_orb,(0,0),rl_orb);d=ImageDraw.Draw(img)
 tf=_f(18);hstr=str(now.hour) if time_format=="24h" else str(now.hour%12 or 12);mstr=now.strftime("%M")
 hf=_f(142);cm=Image.new("L",(360,360),0);cmd=ImageDraw.Draw(cm)
 if len(hstr)==2:
  w0=cmd.textlength(hstr[:1],font=hf);w1=cmd.textlength(hstr[1:],font=hf);gap=(-18 if hstr.startswith("2") else -24);tot=w0+w1+gap;sx0=180-tot/2
  cmd.text((sx0,180),hstr[:1],fill=255,font=hf,anchor="lm");cmd.text((sx0+w0+gap,180),hstr[1:],fill=255,font=hf,anchor="lm")
 else:
  bx0,by0,bx1,by1=cmd.textbbox((0,0),hstr,font=hf);cmd.text((180-(bx0+bx1)//2,180-(by0+by1)//2),hstr,fill=255,font=hf)
 base=cm.filter(ImageFilter.MaxFilter(5))
 g1=base.filter(ImageFilter.GaussianBlur(14)).point(lambda v:min(255,int(v*0.90)))
 g2=base.filter(ImageFilter.GaussianBlur(36)).point(lambda v:min(255,int(v*0.75)))
 g3=base.filter(ImageFilter.GaussianBlur(68)).point(lambda v:min(255,int(v*0.70)))
 g4=base.filter(ImageFilter.GaussianBlur(105)).point(lambda v:min(255,int(v*0.65)))
 g_a=ImageChops.subtract(ImageChops.add(ImageChops.add(ImageChops.add(g1,g2),g3),g4),cm)
 gl=Image.new("RGBA",(360,360),(255,253,245,0) if is_day else (195,220,255,0));gl.putalpha(g_a)
 m_col=(245,248,255)
 hl=Image.new("RGBA",(360,360),(0,0,0,0));hd=ImageDraw.Draw(hl)
 [hd.line([(180+(orb_r*(i/24.0))*math.cos(ma),180+(orb_r*(i/24.0))*math.sin(ma)),(180+(orb_r*((i+1)/24.0))*math.cos(ma),180+(orb_r*((i+1)/24.0))*math.sin(ma))],fill=m_col+(int(245*((i/24.0)**1.5)),),width=3) for i in range(24)]
 hl.putalpha(ImageChops.subtract(hl.getchannel("A"),cm.filter(ImageFilter.MaxFilter(11))))
 img.paste(hl,(cx-180,cy-180),hl);img.paste(gl,(cx-180,cy-180),gl);d=ImageDraw.Draw(img)
 
 d=ImageDraw.Draw(img)
 day_s=now.strftime('%A').upper();num_s=str(now.day);m_deg_b=(math.degrees(ma))%360.0;mo_deg_b=(math.degrees(ma2))%360.0;span_dt=len(day_s)*3.2+14.0;d_min_b=min(abs((m_deg_b-90.0+180.0)%360.0-180.0)-6.0,abs((sa_deg-90.0+180.0)%360.0-180.0)-16.0 if sun_vis>0.02 else 180.0,abs((mo_deg_b-90.0+180.0)%360.0-180.0)-14.0 if mfade>0.08 else 180.0,abs((a_cd-90.0+180.0)%360.0-180.0)-12.0 if cd_vis>0.05 else 180.0);dt_vis=max(0.0,min(1.0,(d_min_b-span_dt)/15.0))
 if show_date and dt_vis>0.03:
  draw_arc_txt(day_s,90.0,orb_r+14,flip=True,bright=True,f_sz=17,step=6.4,alpha_m=dt_vis*0.60)
  draw_arc_txt(num_s,90.0,orb_r-23,flip=True,bright=True,f_sz=36,step=11.0,alpha_m=dt_vis*0.60)
 buf=io.BytesIO();img.save(buf,format="JPEG",quality=92);return "data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")
