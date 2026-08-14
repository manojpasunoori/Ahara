import type { Restaurant } from '@/lib/api';

const searchableTerms=['biryani','ramen','mexican','south indian','chai','mediterranean','salad','pizza','tacos'];
export function restaurantIntent(value:string):string|null{const clean=value.trim().toLowerCase();if(!clean)return null;return searchableTerms.some(term=>clean===term)?clean:null}
export function chipSearch(label:string):string|null{const key=label.toLowerCase();if(key.includes('south indian'))return 'South Indian';if(key.includes('biryani'))return 'biryani';if(key.includes('something light'))return 'salad';if(key.includes('surprise'))return '';return null}
export function resultTitle(query:string,location:string,radius:number):string{return query?`${query} around ${location}`:`Places around ${location} within ${radius} miles`}
export function clearResultsOnLocationChange<T>():T|undefined{return undefined}
export function hasRestaurantMetadata(restaurant:Restaurant):boolean{return restaurant.rating!==null||restaurant.price_level!==null||restaurant.open_now!==null}