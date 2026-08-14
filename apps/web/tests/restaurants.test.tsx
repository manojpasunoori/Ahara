import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { RestaurantCard } from '../components/restaurants/restaurant-card';
import { RestaurantResults } from '../components/restaurants/restaurant-results';
import { chipSearch, clearResultsOnLocationChange, restaurantIntent } from '../lib/restaurants';
import type { Restaurant } from '../lib/api';

const full: Restaurant = { id: 'one', provider: 'demo', name: 'Saffron Leaf', categories: ['South Indian', 'Indian'], latitude: 32.7, longitude: -97.1, address: '112 Garden Way', city: 'Arlington', distance_miles: 1.24, rating: 4.5, review_count: 12, price_level: 2, open_now: true, website: 'https://example.test' };

describe('restaurant discovery UI', () => {
  it('renders factual optional metadata when present', () => {
    const html = renderToStaticMarkup(<RestaurantCard restaurant={full} />);
    expect(html).toContain('4.5 star');
    expect(html).toContain('$$');
    expect(html).toContain('Open');
    expect(html).toContain('Website');
  });
  it('omits unavailable optional metadata', () => {
    const html = renderToStaticMarkup(<RestaurantCard restaurant={{ ...full, rating: null, price_level: null, open_now: null, website: null }} />);
    expect(html).not.toContain('null');
    expect(html).not.toContain('N/A');
    expect(html).not.toContain('Website');
  });
  it('renders loading, empty, and provider unavailable states', () => {
    expect(renderToStaticMarkup(<RestaurantResults state={{ kind: 'loading', location: 'Arlington' }} />)).toContain('Looking around Arlington');
    expect(renderToStaticMarkup(<RestaurantResults state={{ kind: 'empty', query: 'ramen' }} />)).toContain('couldn');
    expect(renderToStaticMarkup(<RestaurantResults state={{ kind: 'error', message: 'Live restaurant discovery unavailable.' }} />)).toContain('unavailable');
  });
  it('maps chips and recognizes simple typed food queries', () => {
    expect(chipSearch('South Indian spice')).toBe('South Indian');
    expect(chipSearch('Biryani mood')).toBe('biryani');
    expect(restaurantIntent('ramen')).toBe('ramen');
    expect(restaurantIntent('find me a quiet place')).toBeNull();
  });
  it('clears stale results on location changes', () => expect(clearResultsOnLocationChange()).toBeUndefined());
});