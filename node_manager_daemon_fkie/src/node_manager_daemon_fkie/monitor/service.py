# Software License Agreement (BSD License)
#
# Copyright (c) 2019, Fraunhofer FKIE/US, Alexander Tiderko
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Fraunhofer nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rospy
import socket
import threading

from diagnostic_msgs.msg import DiagnosticArray
from .cpu_load import CpuLoad
from .cpu_temp import CpuTemp
from .hdd_usage import HddUsage
from .mem_usage import MemUsage
from .net_load import NetLoad


class Service:

    def __init__(self):
        self._mutex = threading.RLock()
        self._diagnostic_rosmsg = DiagnosticArray()
        self._sub_diag_agg = rospy.Subscriber('/diagnostics_agg', DiagnosticArray, self._callback_diagnostics)
        hostname = socket.gethostname()

        self.sensors = []
        self.sensors.append(CpuLoad(hostname, 5.0, 0.9))
        self.sensors.append(CpuTemp(hostname, 5.0, 85.0))
        self.sensors.append(HddUsage(hostname, 30.0, 100.0))
        self.sensors.append(MemUsage(hostname, 5.0, 100.0))
        self.sensors.append(NetLoad(hostname, 3.0, 0.9))

    def _callback_diagnostics(self, msg):
        # TODO: update diagnostics
        self._diagnostic_rosmsg = msg

    def get_system_diagnostics(self, filter_level=0, filter_ts=0):
        result = DiagnosticArray()
        with self._mutex:
            result.header.stamp = rospy.Time.now()
            nowsec = result.header.stamp.secs
            for sensor in self.sensors:
                diag_msg = sensor.last_state(nowsec, filter_level, filter_ts)
                if diag_msg is not None:
                    result.status.append(diag_msg)
        return result

    def get_diagnostics(self, filter_level=0, filter_ts=0):
        # TODO:
        return self._diagnostic_rosmsg

    def stop(self):
        with self._mutex:
            for sensor in self.sensors:
                sensor.cancel_timer()
