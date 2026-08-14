from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app

def payload(): return {'current':{'temperature_2m':90,'apparent_temperature':95,'weather_code':0,'precipitation':0},'daily':{'temperature_2m_max':[92],'temperature_2m_min':[70]},'timezone':'America/Chicago'}
def test_weather_cache_miss_writes_result(monkeypatch):
 cache=Mock();cache.get.return_value=None
 with patch('app.api.context.create_redis_client',return_value=cache),patch('app.api.context.httpx.get') as get:
  get.return_value.json.return_value=payload();r=TestClient(app).get('/api/v1/context/weather?latitude=32.73&longitude=-97.10')
 assert r.status_code==200;cache.setex.assert_called_once();get.assert_called_once()
def test_weather_cache_hit_skips_http():
 cache=Mock();cache.get.return_value='{"temperature":1}'
 with patch('app.api.context.create_redis_client',return_value=cache),patch('app.api.context.httpx.get') as get:
  r=TestClient(app).get('/api/v1/context/weather?latitude=32.73&longitude=-97.10')
 assert r.json()['temperature']==1;get.assert_not_called()
def test_redis_failures_fall_back(monkeypatch):
 cache=Mock();cache.get.side_effect=RuntimeError()
 with patch('app.api.context.create_redis_client',return_value=cache),patch('app.api.context.httpx.get') as get:
  get.return_value.json.return_value=payload();assert TestClient(app).get('/api/v1/context/weather?latitude=32.73&longitude=-97.10').status_code==200
def test_demo_weather_no_network(monkeypatch):
 monkeypatch.setattr('app.api.context.get_settings',lambda: type('S',(),{'ahara_mode':'demo'})())
 with patch('app.api.context.httpx.get') as get: assert TestClient(app).get('/api/v1/context/weather?latitude=1&longitude=1').json()['temperature']==94;get.assert_not_called()
