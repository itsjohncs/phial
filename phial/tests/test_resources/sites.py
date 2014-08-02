# stdlib
import pkg_resources
import os


def get_site_dir(name=None):
    """Return a path containing a site.

    Will extract the site's directory if necessary (if we're in a zip file).
    If ``None`` is given for ``name``, a path to the ``sites_dir/`` directory
    will be returned.
    """
    sites_dir = pkg_resources.resource_filename(
        "phial.tests.test_resources", "sites_dir")
    if not os.path.exists(sites_dir):
        raise RuntimeError(
            "Could not find sites directory at {}.".format(sites_dir))

    if name is None:
        return sites_dir
    else:
        result = os.path.join(sites_dir, name)
        if not os.path.exists(result):
            raise ValueError("Could not find site %s." % (name, ))

        return result


def list_sites():
    """Return a list of all of the test sites available.

    >>> list_sites()
    ["simple", "readme"]
    """
    return os.listdir(get_site_dir())
