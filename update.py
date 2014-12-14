# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import datetime, time
import urllib2
import re
import os, subprocess

import settings

def scrapNova(sdate):
    mainUrl = "http://www.novaplanet.com/radionova/cetaitquoicetitre/"
    step = datetime.timedelta(0, 3600)
    curr_datetime = sdate
    now = datetime.datetime.now()

    fullPlaylist = dict()
    while curr_datetime < now + step:
        url = mainUrl + str(int(time.mktime(curr_datetime.timetuple())))

        try:
            page = urllib2.urlopen(url,timeout=15)
        except Exception as e:
            print(e)

        content = ''.join(page.readlines("utf8"))

        parsed_content = BeautifulSoup(content)
        for t in parsed_content.find_all('div', class_="resultat"):
            try:
                fullPlaylist[(t['class'][0]).split('_')[1]] = {"artist": (t.h2.string if t.h2.string else t.h2.a.string).strip(),
                                                               "title": (t.h3.string if t.h3.string else t.h3.a.string).strip()}
            except:
                print 'Fail'

        curr_datetime += step

    return fullPlaylist


def buildPlaylist(playlist, N):
    counts = dict()
    for diff in playlist.keys():
        song = playlist[diff]['artist'] + ' ' + playlist[diff]['title']
        if song in counts.keys():
            counts[song] += 1
        else:
            counts[song] = 1

    return sorted(counts, key=counts.get, reverse=True)[:N]


def scrapYouTube(song):
    mainUrl = "http://www.youtube.com/results?search_query="
    search_query = '+'.join(song.split(' ')).lower()

    url = mainUrl + search_query
    page = urllib2.urlopen(url,timeout=15)
    content = ''.join(page.readlines("utf8"))

    if len(re.findall('Aucune vid',content))>0:
        print("Aucune video trouvee")
        return ''
    else:
        videos = re.findall('href="\/watch\?v=(.*?)[&;"]',content)
        track_video = videos[0]
        return track_video


def downloadMP3(ytList):
    f = open('todo', 'w')
    for yt in ytList:
        f.write('https://www.youtube.com/watch?v=' + yt + '\n')
    f.close()
    os.system("/usr/bin/youtube-dl -a todo -x")
    os.remove('todo')

def makePlaylistFile():
    audioFiles = os.listdir(os.getcwd())
    f = open('nova-playlist.m3u','w')
    for af in audioFiles:
        f.write(af + '\n')
    f.close()

def syncDropBox(folder):
    subprocess.call("bash dropbox_uploader.sh upload musiques .")


if __name__ == "__main__":

    print "Update de nova-playlist"

    sdate = datetime.datetime.now() - settings.LOOKBACK
    print "Scrap depuis " + str(sdate)
    fullNovaPlaylist = scrapNova(sdate)

    print "Construit la playlist de " + str(settings.NB_TITLES) + " titres"
    targetPlaylist = buildPlaylist(fullNovaPlaylist, settings.NB_TITLES)

    print "Récupère les liens YouTube"
    targetYT = [scrapYouTube(song) for song in targetPlaylist]

    print "Clean les anciens et télécharge les nouveaux .mp3"
    os.chdir('musiques')
    rm = [os.remove(f) for f in os.listdir(os.getcwd())]
    downloadMP3(targetYT)

    print "Construit le fichier de playlist"
    makePlaylistFile()

    print "Synchronise avec DropBox"
    os.chdir('..')
    syncDropBox()

    print "Terminé !"
