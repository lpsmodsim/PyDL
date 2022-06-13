"""Collection of Unit tests for AHPGraph DeviceGraph."""

from AHPGraph import *
from test import *
from Devices import *


def AttributeTest() -> bool:
    """Test of DeviceGraph with attributes."""
    t = test('AttributeTest')

    attr = {'a1': 1, 'a2': 'blue', 'a3': False}
    graph = DeviceGraph(attr)
    t.test(graph.attr == attr, 'attr')

    return t.finish()


def AddDeviceTest() -> bool:
    """Test of adding Devices to a DeviceGraph."""
    t = test('AddDeviceTest')
    graph = DeviceGraph()

    ltd = LibraryTestDevice('ltd')
    sub1 = LibraryTestDevice('sub1')
    sub2 = LibraryTestDevice('sub2')
    sub11 = LibraryTestDevice('sub11')
    sub1.add_submodule(sub11, 'slot')
    ltd.add_submodule(sub1, 'slot', 1)
    ltd.add_submodule(sub2, 'slot', 2)
    graph.add(ltd)

    t.test(len(graph.devices) == 4, 'num devices')
    t.test(ltd in graph.devices, 'get device')
    t.test(sub1 in graph.devices, 'get device')
    t.test(sub2 in graph.devices, 'get device')
    t.test(sub11 in graph.devices, 'get device')

    ltd = LibraryTestDevice()
    graph.add(ltd)
    graph.add(ltd)
    t.test(len(graph.devices) == 5, 'duplicate add')

    sameName = None
    try:
        graph.add(LibraryTestDevice())
        sameName = False
    except RuntimeError:
        sameName = True
    t.test(sameName, 'same name')

    return t.finish()


def CountDevicesTest() -> bool:
    """Test of counting Devices in a DeviceGraph."""
    t = test('CountDevicesTest')
    graph = DeviceGraph()

    devs = dict()
    for i in range(10):
        for j in range(3):
            devs[f'mtd{i}.{j}'] = ModelTestDevice(f'model{i}',
                                                  f'mtd{i}.{j}')
            graph.add(devs[f'mtd{i}.{j}'])

    t.test(len(graph.devices) == 30, 'num devices')
    t.test(devs['mtd0.0'] in graph.devices, 'get device')
    c = graph.count_devices()
    t.test(len(c) == 10, 'device count length')
    t.test(c[devs['mtd0.0'].get_category()] == 3, 'device count length')

    return t.finish()


def CheckPartitionTest() -> bool:
    """Test of checking partition info in a DeviceGraph."""
    t = test('CheckPartitionTest')
    graph = DeviceGraph()

    devs = dict()
    for i in range(10):
        for j in range(3):
            devs[f'mtd{i}.{j}'] = ModelTestDevice(f'model{i}',
                                                  f'mtd{i}.{j}')
            devs[f'mtd{i}.{j}'].set_partition(i, j)
            graph.add(devs[f'mtd{i}.{j}'])

    partitionIncluded = None
    try:
        graph.check_partition()
        partitionIncluded = True
    except RuntimeError:
        partitionIncluded = False
    t.test(partitionIncluded, 'correct partitioning')

    graph.add(LibraryTestDevice())
    partitionIncluded = None
    try:
        graph.check_partition()
        partitionIncluded = False
    except RuntimeError:
        partitionIncluded = True
    t.test(partitionIncluded, 'missing partitioning')

    return t.finish()


def LinkTest() -> bool:
    """Test of linking Devices in a DeviceGraph."""
    t = test('LinkTest')
    graph = DeviceGraph()

    ptd0 = PortTestDevice(0)
    ptd1 = PortTestDevice(1)
    ltd = LibraryTestDevice()
    lptd = LibraryPortTestDevice()
    ltd.add_submodule(lptd, 'slot')

    graph.link(lptd.input, ptd0.optional)
    t.test(len(graph.devices) == 3, 'linking add submodule parent')
    t.test(ltd in graph.devices, 'submodule parent included')
    t.test(graph.links[frozenset({lptd.input, ptd0.optional})] == '0s',
           'default latency')
    linkAgain = None
    try:
        graph.link(ptd0.optional, lptd.input)
        linkAgain = False
    except RuntimeError:
        linkAgain = True
    t.test(linkAgain, 'link again with ports reversed')
    callablePort = None
    try:
        graph.link(ptd0.limit, ptd1.no_limit)
        callablePort = False
    except RuntimeError:
        callablePort = True
    t.test(callablePort, 'forgot to include port num on multi port')
    typeMismatch = None
    try:
        graph.link(ptd0.default, ptd1.ptype)
        typeMismatch = False
    except RuntimeError:
        typeMismatch = True
    t.test(typeMismatch, 'port type mismatch')
    changeSinglePortLink = None
    try:
        graph.link(ptd0.optional, ptd1.optional)
        changeSinglePortLink = False
    except RuntimeError:
        changeSinglePortLink = True
    t.test(changeSinglePortLink, 'linking from a single port again')
    graph.link(ptd0.limit(0), ptd1.limit(0), '123ns')
    t.test(graph.links[frozenset({ptd0.limit(0), ptd1.limit(0)})] == '123ns',
           'latency')

    return t.finish()


def VerifyLinksTest() -> bool:
    """Test of verifying links in a DeviceGraph."""
    t = test('VerifyLinksTest')
    graph = DeviceGraph()

    ptd0 = PortTestDevice(0)
    ptd1 = PortTestDevice(1)
    ltd = LibraryTestDevice()
    lptd = LibraryPortTestDevice()
    ltd.add_submodule(lptd, 'slot')

    graph.link(lptd.input, ptd0.optional)
    graph.link(lptd.output, ptd1.optional)
    graph.link(ptd0.default, ptd1.default)
    graph.link(ptd0.ptype, ptd1.ptype)
    graph.link(ptd0.no_limit(0), ptd1.no_limit(0))
    graph.link(ptd0.limit(0), ptd1.limit(0))
    verified = None
    try:
        graph.verify_links()
        verified = False
    except RuntimeError:
        verified = True
    t.test(verified, 'not all required ports connected')

    graph.link(ptd0.format(0), ptd1.format(0))
    verified = None
    try:
        graph.verify_links()
        verified = True
    except RuntimeError:
        verified = False
    t.test(verified, 'verified all required ports have at least 1 connection')

    return t.finish()


def FollowLinksTest() -> bool:
    """Test of following links by rank in a DeviceGraph."""
    t = test('FollowLinksTest')
    graph = DeviceGraph()
    levels = 2

    ratd0 = RecursiveAssemblyTestDevice(levels, 0)
    ratd1 = RecursiveAssemblyTestDevice(levels, 1)
    lptd0 = LibraryPortTestDevice(0)
    lptd1 = LibraryPortTestDevice(1)

    # complete the rings
    graph.link(ratd0.input, ratd0.output)
    graph.link(ratd1.input, ratd1.output)

    graph.link(lptd0.input, lptd1.output)
    graph.link(lptd1.input, lptd0.output)
    for i in range(2 ** (levels+1)):
        graph.link(lptd0.optional(None), ratd0.optional(None))
        graph.link(lptd1.optional(None), ratd1.optional(None))

    ratd0.set_partition(0)
    ratd1.set_partition(1)
    lptd0.set_partition(2)
    lptd1.set_partition(2)

    graph.follow_links(0)
    for dev in graph.devices:
        if dev.library is None:
            t.test(dev.name == f'RecursiveAssemblyTestDevice{levels}1',
                   'only one assembly left')
        else:
            t.test(dev.library is not None, 'library set')

    return t.finish()


def FlattenTest() -> bool:
    """Test of flattening a DeviceGraph."""
    t = test('FlattenTest')
    levels = 6

    def createGraph() -> DeviceGraph:
        """Create a graph for testing."""
        graph = DeviceGraph()

        ratd0 = RecursiveAssemblyTestDevice(levels, 0)
        ratd1 = RecursiveAssemblyTestDevice(levels, 1)
        lptd0 = LibraryPortTestDevice(0)
        lptd1 = LibraryPortTestDevice(1)

        # complete the rings
        graph.link(ratd0.input, ratd0.output)
        graph.link(ratd1.input, ratd1.output)

        graph.link(lptd0.input, lptd1.output)
        graph.link(lptd1.input, lptd0.output)
        for i in range(2 ** (levels+1)):
            graph.link(lptd0.optional(None), ratd0.optional(None))
            graph.link(lptd1.optional(None), ratd1.optional(None))

        ratd0.set_partition(0)
        ratd1.set_partition(1)
        lptd0.set_partition(2)
        lptd1.set_partition(2)
        return graph, ratd0

    flat, _ = createGraph()
    flat.flatten()
    t.test(not any([d.library is None for d in flat.devices]),
           'no assemblies left')

    twoLevels, _ = createGraph()
    twoLevels.flatten(2)
    t.test([d.library is None for d in twoLevels.devices].count(True) == 8,
           'correct number of assemblies left')

    byName, _ = createGraph()
    byName.flatten(name=f'RecursiveAssemblyTestDevice{levels}0')
    rank0, _ = createGraph()
    rank0.flatten(rank=0)
    t.test(byName.names == rank0.names, 'name and rank devices')

    byNameLinks = set()
    rankLinks = set()
    for link in byName.links:
        for port in link:
            byNameLinks.add(str(port))
    for link in rank0.links:
        for port in link:
            rankLinks.add(str(port))
    t.test(byNameLinks == rankLinks, 'name and rank links')

    expand, ratd0 = createGraph()
    expand.flatten(expand={ratd0})
    assemblies = [d.library is None for d in expand.devices]
    t.test(assemblies.count(True) == 3, 'correct number of assemblies left')

    return t.finish()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='AHPGraph DeviceGraph unittests')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='show detailed output')
    args = parser.parse_args()
    test.verbose = args.verbose

    results = [AttributeTest(),
               AddDeviceTest(),
               CountDevicesTest(),
               CheckPartitionTest(),
               LinkTest(),
               VerifyLinksTest(),
               FollowLinksTest(),
               FlattenTest()]

    exit(1 if True in results else 0)
