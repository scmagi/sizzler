#!/usr/bin/env python3

import os
import pwd
import grp


class RootPriviledgeManager:

    def isRoot(self):
        return os.geteuid() == 0

    def dropRoot(self):
        if not self.isRoot(): return True

        try:
            user, group = ("nobody", "nogroup")

            uid = pwd.getpwnam(user).pw_uid
            gid = grp.getgrnam(group).gr_gid

            os.setgroups([]) # Remove group privileges

            os.setgid(gid)
            os.setuid(uid)

            old_umask = os.umask(0o077)
        except:
            if self.isRoot():
                raise Exception("Failed dropping root to nobody:nogroup.")

        return not self.isRoot()
