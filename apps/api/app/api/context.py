import httpx
from fastapi import APIRouter, HTTPException, Query
from app.core.cache import create_redis_client
from app.core.config import get_settings
router=APIRouter(prefix='/api/v1',tags=['context'])
def key(lat:float,lon:float)->str:return f'weather:{lat:.2f}:{lon:.2f}:f'
@router.get('/context/weather')
def weather(latitude:float=Query(ge=-90,le=90),longitude:float=Query(ge=-180,le=180)):
 if get_settings().ahara_mode=='demo':return {'temperature':94,'feels_like':99,'unit':'F','condition':'sunny','weather_code':0,'precipitation':0,'daily_high':97,'daily_low':78,'timezone':'America/Chicago','temperature_band':'hot','comfort_context':'stay_cool'}
 cache=None
 try:
  cache=create_redis_client(); hit=cache.get(key(latitude,longitude))
  if hit:return __import__('json').loads(hit)
 except Exception: cache=None
 try:
  data=httpx.get('https://api.open-meteo.com/v1/forecast',params={'latitude':latitude,'longitude':longitude,'current':'temperature_2m,apparent_temperature,weather_code,precipitation','daily':'temperature_2m_max,temperature_2m_min','timezone':'auto','temperature_unit':'fahrenheit'},timeout=8).json();c=data['current'];d=data['daily'];t=c['temperature_2m'];out={'temperature':t,'feels_like':c['apparent_temperature'],'unit':'F','condition':'sunny' if c['weather_code']==0 else 'rainy' if c['precipitation']>0 else 'cloudy','weather_code':c['weather_code'],'precipitation':c['precipitation'],'daily_high':d['temperature_2m_max'][0],'daily_low':d['temperature_2m_min'][0],'timezone':data['timezone'],'temperature_band':'hot' if t>=85 else 'cold' if t<50 else 'comfortable','comfort_context':'stay_cool' if t>=85 else 'warm_up' if t<50 else 'get_out'}
  if cache:
   try: cache.setex(key(latitude,longitude),600,__import__('json').dumps(out))
   except Exception: pass
  return out
 except Exception as e: raise HTTPException(503,'Weather is unavailable right now') from e
