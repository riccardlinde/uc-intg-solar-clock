#!/usr/bin/env python3
import asyncio,json,logging,os
from datetime import datetime
import ucapi
from ucapi import media_player
from uc_intg_analog_clock.clock_renderer import render_analog_clock_base64,_solar
logging.basicConfig(level=logging.INFO)
loop=asyncio.new_event_loop();asyncio.set_event_loop(loop);api=ucapi.IntegrationAPI(loop)
CONFIG_DIR=os.getenv("UC_CONFIG_HOME",".");CONFIG_FILE=os.path.join(CONFIG_DIR,"config.json");ENTITY_ID="analog_clock_main"
config={"latitude":41.39,"longitude":2.16,"time_format":"24h","temp_unit":"C","show_moon":True,"show_temp":True,"show_sun_events":True,"show_date":True}
clock_task=None
def _b(v,d=True):return v if isinstance(v,bool) else (v.lower() in("true","1","yes","on") if isinstance(v,str) else d)
def get_attrs():
 now=datetime.now();lat=float(config.get("latitude",41.39));lon=float(config.get("longitude",2.16));unit=config.get("temp_unit","C");tfmt=config.get("time_format","24h")
 uri=render_analog_clock_base64(now,show_date=_b(config.get("show_date",True)),time_format=tfmt,temp_unit=unit,show_moon=_b(config.get("show_moon",True)),show_temp=_b(config.get("show_temp",True)),show_sun_events=_b(config.get("show_sun_events",True)),latitude=lat,longitude=lon)
 sc=_solar(lat,lon,unit);td=now.strftime("%H:%M") if tfmt=="24h" else now.strftime("%I:%M %p").lstrip("0");hr=now.hour+now.minute/60.0;iday=(sc["sr"]<=hr<sc["ss"]);ehr=sc["ss"] if iday else sc["sr"];elbl="Sunset" if iday else "Sunrise";estr=f"{int(ehr):02d}:{int(round((ehr%1)*60)):02d}"
 return {media_player.Attributes.STATE:media_player.States.ON,media_player.Attributes.MEDIA_TITLE:f"{td}  ·  {now.strftime('%A %d')}",media_player.Attributes.MEDIA_ARTIST:f"{sc.get('temp','')}°{unit}  ·  {elbl} {estr}",media_player.Attributes.MEDIA_IMAGE_URL:uri}
def load_config():
 if os.path.exists(CONFIG_FILE):
  try:
   with open(CONFIG_FILE,"r",encoding="utf-8") as f:config.update(json.load(f))
  except Exception:pass
def save_config():
 os.makedirs(CONFIG_DIR,exist_ok=True)
 with open(CONFIG_FILE,"w",encoding="utf-8") as f:json.dump(config,f,indent=2)
async def cmd_handler(entity,cmd_id,params):return ucapi.StatusCodes.OK
def create_clock_entity():return media_player.MediaPlayer(ENTITY_ID,{"en":"Solar & Lunar Clock"},features=[],attributes=get_attrs(),device_class=media_player.DeviceClasses.RECEIVER,cmd_handler=cmd_handler)
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
async def on_sub(eids):
 global clock_task
 if ENTITY_ID in eids:
  await push_clock_update()
  if clock_task is None or clock_task.done():clock_task=loop.create_task(clock_loop())
@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsub(eids):
 global clock_task
 if ENTITY_ID in eids and clock_task and not clock_task.done():clock_task.cancel();clock_task=None
async def setup_handler(msg):
 if isinstance(msg,ucapi.DriverSetupRequest):
  sd=msg.setup_data
  for k,dv in(("latitude",41.39),("longitude",2.16)):
   try:config[k]=float(sd.get(k,dv))
   except Exception:config[k]=dv
  config["time_format"]=sd.get("time_format","24h");config["temp_unit"]=sd.get("temp_unit","C")
  for k in("show_moon","show_temp","show_sun_events","show_date"):config[k]=_b(sd.get(k,True))
  save_config();api.available_entities.clear();api.available_entities.add(create_clock_entity());return ucapi.SetupComplete()
 return ucapi.SetupComplete()
async def main():load_config();api.available_entities.add(create_clock_entity());await api.init("driver.json",setup_handler)
if __name__=="__main__":loop.run_until_complete(main());loop.run_forever()
