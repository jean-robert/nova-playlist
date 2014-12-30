# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import datetime, time
import urllib2
import re
import os, subprocess
import logging

import settings

def scrapNova(sdate):
    mainUrl = "http://www.novaplanet.com/radionova/cetaitquoicetitre/"
    step = datetime.timedelta(0, 3600)
    curr_datetime = sdate
    now = datetime.datetime.now()

    fullPlaylist = dict()
    while curr_datetime < now + step:
        logger.info('Scrap actuellement @ ' + str(curr_datetime))
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
    final = sorted(counts, key=counts.get, reverse=True)[:N]
    for i in range(N):
        logger.info('#' + str(i + 1) + ': ' + final[i])
    return final


def scrapYouTube(song):
    mainUrl = "http://www.youtube.com/results?search_query="
    search_query = '+'.join(song.split(' ')).lower()

    url = mainUrl + search_query
    page = urllib2.urlopen(url,timeout=15)
    content = ''.join(page.readlines("utf8"))

    if len(re.findall('Aucune vid',content))>0:
        logger.warn(song + " : Aucune video trouvee")
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
    logger.info('Debut des telechargements...')
    os.system("/usr/bin/youtube-dl -q -a todo -x")
    logger.info('Telechargements finis')
    os.remove('todo')

def makePlaylistFile():
    audioFiles = os.listdir(os.getcwd())
    f = open('nova-playlist.m3u','w')
    for af in audioFiles:
        f.write(af + '\n')
    f.close()

def syncDropBox():
    logger.info('Debut de la synchronisation DropxBox...')
    subprocess.call("bash dropbox_uploader.sh delete musiques")
    subprocess.call("bash dropbox_uploader.sh upload musiques .")
    logger.info('Synchronisation DropxBox finie...')

if __name__ == "__main__":

    logger = logging.getLogger('[nova-playlist]')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info("Update de nova-playlist")

    sdate = datetime.datetime.now() - settings.LOOKBACK
    logger.info("Scrap depuis " + str(sdate))
    fullNovaPlaylist = scrapNova(sdate)

    logger.info("Construit la playlist de " + str(settings.NB_TITLES) + " titres")
    targetPlaylist = buildPlaylist(fullNovaPlaylist, settings.NB_TITLES)

    logger.info("Récupère les liens YouTube")
    targetYT = [scrapYouTube(song) for song in targetPlaylist]

    logger.info("Clean les anciens et télécharge les nouveaux .mp3")
    os.chdir('musiques')
    rm = [os.remove(f) for f in os.listdir(os.getcwd())]
    downloadMP3(targetYT)

    logger.info("Construit le fichier de playlist")
    makePlaylistFile()

    os.chdir('..')
    syncDropBox()

    logger.info("Update terminé !")
