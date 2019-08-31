python-hilink
=============

python-hilink is a Python 3 library for managing HiLink-enabled Huawei Routers.

Unlike other implementations, this version has no external dependencies and so 
only uses the standard library for its operation. This means that you can use 
it on embedded systems like an OpenWRT router with no other requirement than 
a Python 3 interpreter.

The library can be used for virtually any operation your HiLink-enabled Huawei 
router supports although future versions will directly include some of these 
operations for easier usage.

### lte_mode

lte_mode is a utility script I wrote using the hilink library for a specific 
usecase: if you're looking for a tool that would encourage your router to stay 
connected in LTE mode, this is the script for you. It works by first checking 
if the router is currently in LTE mode and does nothing if it is. If it is not, 
it will force a 4G (LTE) only mode and then, shortly after, revert to auto. 
This has the effect of nudging the router to stay connected in LTE mode. The 
reason to not simply force 4G-only mode is that the router tends to disconnect 
completely from the network if it is temporarily unable to connect to the base 
station on an LTE band and so this hack nudges it to connect and stay connected 
in LTE mode as long as there's a signal.

You may use the `lte_mode` script with something like `cron` to monitor your 
router and keep it connected in LTE mode.

Usage:

`$ lte_mode router_ip router_username router_password`

It will print out `OK` if the router is already in LTE mode or `RESET` if it 
wasn't but it successfully reset it to LTE mode.

### reboot_on_disconnect

`reboot_on_disconnect` is a helper script for rebooting the router whenever it 
detects that the router is offline. It could also be added to a task scheduler 
to automatically reboot the router if it was disconnected from the network. 
Rather than having to monitor the router yourself and auto-restart, you can 
delegate that to this script and it would reboot the router as necessary.

With a little tweak, the script could be made to force a reboot of the router 
if (despite being connected to the network) there is no internet connection.
