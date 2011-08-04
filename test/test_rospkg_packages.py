# Software License Agreement (BSD License)
#
# Copyright (c) 2011, Willow Garage, Inc.
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
#  * Neither the name of Willow Garage, Inc. nor the names of its
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

from __future__ import print_function

import os
import sys
import time
  
def test_RosPack_constructor():
    from rospkg import RosPack

    r = RosPack()
    assert r.ros_root == os.environ.get('ROS_ROOT', None)
    assert r.ros_package_path == os.environ.get('ROS_PACKAGE_PATH', None)

    import tempfile
    tmp = tempfile.gettempdir()

    r = RosPack(ros_root=tmp)
    assert r.ros_root == tmp
    assert r.ros_package_path == os.environ.get('ROS_PACKAGE_PATH', None)
    
    r = RosPack(ros_package_path=tmp)
    assert r.ros_root == os.environ.get('ROS_ROOT', None)
    assert r.ros_package_path == tmp

import subprocess
def rospackexec(args):
    rospack_bin = os.path.join(os.environ['ROS_ROOT'], 'bin', 'rospack')
    val = (subprocess.Popen([rospack_bin] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0] or '').strip()
    if val.startswith('rospack:'): #rospack error message
        raise Exception(val)
    return val

# for comparing against 'ground truth'
def rospack_list():
    return [s.split()[0] for s in rospackexec(['list']).split('\n')]
def rospack_find(package):
    return rospackexec(['find', package]).strip()
def rospack_depends(package):
    return unicode(rospackexec(['depends', package])).split()
def rospack_depends1(package):
    return unicode(rospackexec(['depends1', package])).split()

def test_RosPack_list_packages():
    from rospkg import RosPack
    r = RosPack()

    pkgs = rospack_list()
    retval = r.list_packages()
    assert set(pkgs) == set(retval), "%s vs %s"%(pkg, retval)
    
    # test twice for caching
    retval = r.list_packages()
    assert set(pkgs) == set(retval), "%s vs %s"%(pkg, retval)

def get_package_test_path():
    return os.path.abspath(os.path.join(sys.path[0], 'package_tests'))

def test_RosPack_get_path():
    from rospkg import RosPack, PackageNotFound, InvalidPackage

    path = get_package_test_path()
    foo_path = os.path.join(path, 'p1', 'foo')
    bar_path = os.path.join(path, 'p1', 'bar')
    baz_path = os.path.join(path, 'p2', 'baz')
    
    # point ROS_ROOT at top, should spider entire tree
    print("ROS_ROOT: %s"%(path))
    print("ROS_PACKAGE_PATH: ")
    r = RosPack(ros_root=path, ros_package_path='')
    assert foo_path == r.get_path('foo')
    assert bar_path == r.get_path('bar')
    assert baz_path == r.get_path('baz')
    try:
        r.get_path('fake')
        assert False
    except PackageNotFound:
        pass
    
    # divide tree in half to test precedence
    print("ROS_ROOT: %s"%(os.path.join(path, 'p1')))
    print("ROS_PACKAGE_PATH: %s"%(os.path.join(path, 'p2')))
    r = RosPack(ros_root=os.path.join(path, 'p1'), ros_package_path=os.path.join(path, 'p2'))
    assert foo_path == r.get_path('foo'), "%s vs. %s"%(foo_path, r.get_path('foo'))
    assert bar_path == r.get_path('bar')
    assert baz_path == r.get_path('baz')

    # stresstest against rospack
    r = RosPack()
    for p in rospack_list():
        retval = r.get_path(p)
        rospackval = rospack_find(p)
        assert retval == rospackval, "[%s]: %s vs. %s"%(p, retval, rospackval)

def test_RosPackage_get_depends():
    from rospkg import RosPack, PackageNotFound, InvalidPackage
    path = get_package_test_path()
    r = RosPack(ros_root=path, ros_package_path='')

    # TODO: need one more step
    assert set(r.get_depends('baz')) == set(['foo', 'bar'])
    assert r.get_depends('bar') == ['foo']
    assert r.get_depends('foo') == []

    # stress test: test default environment against rospack
    r = RosPack()
    m = r.get_manifest('xmlrpcpp')
    
    for p in rospack_list():
        retval = set(r.get_depends(p))
        rospackval = set(rospack_depends(p))
        assert retval == rospackval, "[%s]: %s vs. %s"%(p, retval, rospackval)
    
def test_RosPackage_get_direct_depends():
    from rospkg import RosPack, PackageNotFound, InvalidPackage
    path = get_package_test_path()
    r = RosPack(ros_root=path, ros_package_path='')

    assert set(r.get_direct_depends('baz')) == set(['bar', 'foo'])
    assert r.get_direct_depends('bar') == ['foo']
    assert r.get_direct_depends('foo') == []

    # stress test: test default environment against rospack
    r = RosPack()
    for p in rospack_list():
        retval = set(r.get_direct_depends(p))
        rospackval = set(rospack_depends1(p))
        assert retval == rospackval, "[%s]: %s vs. %s"%(p, retval, rospackval)
