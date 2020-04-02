#!/usr/bin/env python3

import asyncio
import ssl
import certifi

from datetime import datetime
from aiohttp import ClientSession, TCPConnector
from volvooncall import __version__, Connection
from volvooncall.util import read_config
from volvooncall.dashboard import Position, JournalLastTrip

MEASUREMENT='volvooncall'

def to_timestamp(dt):
  return str(int(dt.timestamp() * 1000000000))

async def main():
  config = read_config()
  # ensure this script does not apply changes
  config.update(mutable=False)

  async with ClientSession() as session:
    connection = Connection(session, **config)

    res = await connection.update()
    if res:
      for vehicle in connection.vehicles:
        tags = []
        if vehicle.registration_number:
          tags += ['registration_number=%s' % (vehicle.registration_number)]

        measurements = []
        other_measurements = []

        dashboard = vehicle.dashboard()
        for instrument in dashboard.instruments:
          name = instrument.attr.replace('.', '_')

          # extract position as different measurement so the date from position is stored correctly
          if isinstance(instrument, Position):
            other_measurement = [
              '%s_lat=%s' % (name, instrument.state[0]),
              '%s_lon=%s' % (name, instrument.state[1]),
            ]
            if instrument.state[3] != None:
              other_measurements += [[instrument.state[3], other_measurement]]
            else:
              other_measurements += [[datetime.now(), other_measurement]]
          elif isinstance(instrument, JournalLastTrip):
            # ignore last trip information if provided
            None
          else:
            measurements += ['%s=%s' % (name  , instrument.state)]

        # format main measurements as single line
        print(
          '%s %s %s' % (
            ','.join([MEASUREMENT, *tags]),
            ','.join(measurements),
            to_timestamp(datetime.now()),
          )
        )

        # format any other measurements as other values to allow different timestamps
        # (i.e. last position is reported along with time of when data was received)
        for other_measurement in other_measurements:
          print(
            '%s %s %s' % (
              ','.join([MEASUREMENT, *tags]),
              ','.join(other_measurement[1]),
              to_timestamp(other_measurement[0]),
            )
          )

try:
  from asyncio import run
except ImportError:
  def run(fut, debug=False):
    loop = asyncio.get_event_loop()
    loop.set_debug(debug)
    loop.run_until_complete(fut)
    loop.close()

  asyncio.create_task = lambda coro: asyncio.get_event_loop().create_task(coro)

run(main())
