import httpx
from fastapi import APIRouter, HTTPException, Query
router=APIRouter(prefix='/api/v1',tags=['context'])
@router.get('/location/resolve')
def resolve_location(query:str=Query(min_length=2,max_length=200)):
 try:
  r=httpx.get('https://geocoding-api.open-meteo.com/v1/search',params={'name':query,'count':1,'language':'en','format':'json'},timeout=8); item=r.json().get('results',[None])[0]
  if not item: raise HTTPException(404,'Location not found')
  admin=item.get('admin1',''); country=item.get('country',''); return {'latitude':item['latitude'],'longitude':item['longitude'],'city':item['name'],'state_or_region':admin,'country':country,'display_name':f"{item['name']}, {admin}" if admin else item['name'],'timezone':item.get('timezone')}
 except HTTPException: raise
 except Exception as e: raise HTTPException(503,'Location resolution is unavailable') from e
