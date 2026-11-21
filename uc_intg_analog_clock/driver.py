#!/usr/bin/env python3
import asyncio,json,logging,os,ssl,urllib.parse,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
import ucapi
from ucapi import media_player
from uc_intg_analog_clock.clock_renderer import render_analog_clock_base64
logging.basicConfig(level=logging.INFO)
loop=asyncio.new_event_loop();asyncio.set_event_loop(loop);api=ucapi.IntegrationAPI(loop)
CONFIG_DIR=os.getenv("UC_CONFIG_HOME",".");CONFIG_FILE=os.path.join(CONFIG_DIR,"config.json");ENTITY_ID="analog_clock_main"
config={"location":"Barcelona","latitude":41.39,"longitude":2.16,"timezone":"Europe/Madrid","time_format":"24h","temp_unit":"C","show_moon":True,"show_temp":True,"show_sun_events":True,"show_date":True}
clock_task=None
def _b(v,d=True):return v if isinstance(v,bool) else (v.lower() in("true","1","yes","on") if isinstance(v,str) else d)
BUILTIN={"barcelona":(41.39,2.16,"Europe/Madrid"),"madrid":(40.42,-3.70,"Europe/Madrid"),"london":(51.51,-0.13,"Europe/London"),"paris":(48.86,2.35,"Europe/Paris"),"berlin":(52.52,13.40,"Europe/Berlin"),"amsterdam":(52.37,4.90,"Europe/Amsterdam"),"rome":(41.90,12.50,"Europe/Rome"),"lisbon":(38.72,-9.14,"Europe/Lisbon"),"zurich":(47.38,8.54,"Europe/Zurich"),"vienna":(48.21,16.37,"Europe/Vienna"),"copenhagen":(55.68,12.57,"Europe/Copenhagen"),"stockholm":(59.33,18.07,"Europe/Stockholm"),"oslo":(59.91,10.75,"Europe/Oslo"),"dublin":(53.35,-6.26,"Europe/Dublin"),"new york":(40.71,-74.01,"America/New_York"),"los angeles":(34.05,-118.24,"America/Los_Angeles"),"chicago":(41.88,-87.63,"America/Chicago"),"toronto":(43.65,-79.38,"America/Toronto"),"tokyo":(35.68,139.65,"Asia/Tokyo"),"sydney":(-33.87,151.21,"Australia/Sydney"),"singapore":(1.35,103.82,"Asia/Singapore"),"dubai":(25.20,55.27,"Asia/Dubai")}
def _geocode(q):
 q=(q or "").strip()
 if not q:return
 if q.lower() in BUILTIN:config["latitude"],config["longitude"],config["timezone"]=BUILTIN[q.lower()];return
 if "," in q:
  pts=q.split(",",1)
  try:config["latitude"],config["longitude"]=float(pts.strip()),float(pts.strip());return
  except Exception:pass
 try:
  url="https://"+"geocoding-api"+"://"+urllib.parse.quote(q)+"&count=1&language=en&format=json"
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
  res=json.loads(urllib.request.urlopen(req,timeout=8,context=ssl._create_unverified_context()).read().decode()).get("results")
  if res:config["latitude"],config["longitude"],config["timezone"]=res["latitude"],res["longitude"],res.get("timezone",config.get("timezone","Europe/Madrid"))
 except Exception as e:logging.warning(f"Geocode failed: {e}")
def get_attrs():
 try:tz=ZoneInfo(config.get("timezone","Europe/Madrid"))
 except Exception:tz=None
 now=datetime.now(tz) if tz else datetime.now()
 uri=render_analog_clock_base64(now,show_date=_b(config.get("show_date",True)),time_format=config.get("time_format","24h"),temp_unit=config.get("temp_unit","C"),show_moon=_b(config.get("show_moon",True)),show_temp=_b(config.get("show_temp",True)),show_sun_events=_b(config.get("show_sun_events",True)),latitude=float(config.get("latitude",41.39)),longitude=float(config.get("longitude",2.16)))
 return {media_player.Attributes.STATE:media_player.States.ON,media_player.Attributes.MEDIA_TITLE:"",media_player.Attributes.MEDIA_ARTIST:"",media_player.Attributes.MEDIA_IMAGE_URL:uri}
def load_config():
 if os.path.exists(CONFIG_FILE):
  try:
   with open(CONFIG_FILE,"r",encoding="utf-8") as f:config.update(json.load(f))
  except Exception:pass
def save_config():
 os.makedirs(CONFIG_DIR,exist_ok=True)
 with open(CONFIG_FILE,"w",encoding="utf-8") as f:json.dump(config,f,indent=2)
async def cmd_handler(entity,cmd_id,params):return ucapi.StatusCodes.OK
def create_clock_entity():return media_player.MediaPlayer(ENTITY_ID,{"en":"Solar & Lunar Clock"},features=[],attributes=get_attrs(),icon="uc:clock",device_class=media_player.DeviceClasses.RECEIVER,cmd_handler=cmd_handler)
async def push_clock_update():
 if api.configured_entities.contains(ENTITY_ID):api.configured_entities.update_attributes(ENTITY_ID,get_attrs())
async def clock_loop():
 while True:
  try:await push_clock_update();await asyncio.sleep(max(1.0,60.0-datetime.now().second))
  except asyncio.CancelledError:break
@api.listens_to(ucapi.Events.CONNECT)
async def on_connect():
 global clock_task
 await api.set_device_state(ucapi.DeviceStates.CONNECTED);await push_clock_update()
 if clock_task is None or clock_task.done():clock_task=loop.create_task(clock_loop())
@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_standby():
 global clock_task
 if clock_task and not clock_task.done():clock_task.cancel();clock_task=None
@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_exit_standby():
 global clock_task
 await push_clock_update()
 if clock_task is None or clock_task.done():clock_task=loop.create_task(clock_loop())
@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_sub(entity_ids):
 global clock_task
 if ENTITY_ID in entity_ids:
  await push_clock_update()
  if clock_task is None or clock_task.done():clock_task=loop.create_task(clock_loop())
@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsub(entity_ids):
 global clock_task
 if ENTITY_ID in entity_ids and clock_task and not clock_task.done():clock_task.cancel();clock_task=None
async def setup_handler(msg):
 if isinstance(msg,ucapi.DriverSetupRequest):
  sd=msg.setup_data;config["location"]=(sd.get("location") or "Barcelona").strip();_geocode(config["location"]);config["time_format"]=sd.get("time_format","24h");config["temp_unit"]=sd.get("temp_unit","C")
  for k in("show_moon","show_temp","show_sun_events","show_date"):config[k]=_b(sd.get(k,True))
  save_config();api.available_entities.clear();api.available_entities.add(create_clock_entity());return ucapi.SetupComplete()
 return ucapi.SetupComplete()
async def main():load_config();api.available_entities.add(create_clock_entity());await api.init("driver.json",setup_handler)
if __name__=="__main__":loop.run_until_complete(main());loop.run_forever()
