# -*- coding: utf-8 -*-

from redis_cache.rediscache import CacheMissException
from geopy import Nominatim


class NominatimWrapper(Nominatim):
    def geocode(self, query, **kwargs):
        kwargs['addressdetails'] = True
        return super(NominatimWrapper, self).geocode(query, **kwargs)


class Geocoder(object):

    @classmethod
    def from_config(cls, config):
        backends = config.get('backends')
        if backends is None:
            raise KeyError("Specify at least one geocoding backend in your config")
        backend_instances = []
        for backend_entry in backends:
            for _, backend in backend_entry.iteritems():
                backend_class = backend['class']
                params = backend.get('params', {})
                backend_instance = backend_class(**params)
                backend_instances.append(backend_instance)

        return cls(backend_instances)

    def __init__(self, backends):
        self.backends = backends

    def geocode(self, address):
        result = None
        for backend in self.backends:
            result = backend.geocode(address)
            if result is not None:
                result = result.raw
                break

        return result


class GeocoderClient(object):
    @classmethod
    def from_config(cls, config):
        cache = config.get('cache')
        if cache is None:
            raise KeyError('Specify a "cache" entry in your config')

        geocoder = Geocoder.from_config(config)

        cache_client = cls(geocoder, cache)
        return cache_client

    def __init__(self, geocoder, cache):
        self.geocoder = geocoder
        self.cache = cache

    def geocode(self, address):
        # TODO: how to handle typos!
        address = address.lower()
        try:
            result = self.cache.get_json(address)
        except CacheMissException:
            result = self.geocoder.geocode(address)
            if result is None:
                raise ValueError("Address not found %s", address)
            self.cache.store_json(address, result)
        return result
