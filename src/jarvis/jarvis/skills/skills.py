import sys
import re
import os
import json
import time
import psutil
import subprocess
import wikipedia
import logging
import requests
from pyowm import OWM
from datetime import datetime
from bs4 import BeautifulSoup as bs
from apscheduler.schedulers.background import BackgroundScheduler

from jarvis.settings import WEATHER_API
from jarvis.utils.response_utils import assistant_response


class Skills:

    @classmethod
    def enable_jarvis(cls, **kwargs):
        """
        Creates the assistant respond according to the datetime hour and
        updates the execute state.
        """
        now = datetime.now()
        day_time = int(now.strftime('%H'))

        if day_time < 12:
            assistant_response('Good morning human')
        elif 12 <= day_time < 18:
            assistant_response('Good afternoon human')
        else:
            assistant_response('Good evening human')
        assistant_response('What do you want to do for you?')

        return {'ready_to_execute': True,
                'enable_time': now}

    @classmethod
    def disable_jarvis(cls, **kargs):
        """
        Shutdown the assistant service
        :param args:
        :return:
        """
        assistant_response('Bye bye!!')
        logging.debug('Application terminated gracefully.')
        sys.exit()

    @classmethod
    def open_website_in_browser(cls, tag, voice_transcript, skill):
        """
        Opens a web page in the browser.
        :param tag: string (e.g 'open')
        :param voice_transcript: string (e.g 'open youtube')

        NOTE: If in the voice_transcript there are more than one commands_dict
        e.g voice_transcript='open youtube and open netflix' the application will find
        and execute only the first one, in our case will open the youtube.
        """
        reg_ex = re.search(tag + ' ([a-zA-Z]+)', voice_transcript)
        try:
            if reg_ex:
                domain = reg_ex.group(1)
                url = cls._create_url(domain)
                assistant_response('Sure')
                subprocess.Popen(["python", "-m",  "webbrowser",  "-t",  url], stdout=subprocess.PIPE)
                time.sleep(1)
                assistant_response('I opened the {0}'.format(domain))
        except Exception as e:
            logging.debug(e)
            assistant_response("I can't find this domain..")

    @classmethod
    def _create_url(cls, tag):
        """
        Creates a url. It checks if there is .com suffix and add it if it not exist.
        :param tag: string (e.g youtube)
        :return: string (e.g http://www.youtube.com)
        """
        if re.search('.com', tag):
            url = 'http://www.' + tag
        else:
            url = 'http://www.' + tag + '.com'
        return url

    @classmethod
    def tell_the_weather(cls, tag, voice_transcript, skill):
        """
        Tells the weather of a place
        :param tag: string (e.g 'weather')
        :param voice_transcript: string (e.g 'weather in London')
        """
        reg_ex = re.search(tag + ' in ([a-zA-Z]+)', voice_transcript)
        try:
            if reg_ex:
                if WEATHER_API['key']:
                    city = reg_ex.group(1)
                    status, temperature = cls._get_weather_status_and_temperature(city)
                    if status and temperature:
                        assistant_response('Current weather in %s is %s.\n'
                                       'The maximum temperature is %0.2f degree celcius. \n'
                                       'The minimum temperature is %0.2f degree celcius.'
                                       % (city, status, temperature['temp_max'], temperature['temp_min'])
                                       )
                    else:
                        assistant_response("Sorry the weather API is not available now..")
                else:
                    assistant_response("Weather forecast is not working.\n"
                                       "You can get an Weather API key from: https://openweathermap.org/appid")
        except Exception as e:
            logging.debug(e)
            print(e)
            assistant_response("I faced an issue with the weather site..")

    @classmethod
    def _get_weather_status_and_temperature(cls, city):
        owm = OWM(API_key=WEATHER_API['key'])
        if owm.is_API_online():
            obs = owm.weather_at_place(city)
            weather = obs.get_weather()
            status = weather.get_status()
            temperature = weather.get_temperature(WEATHER_API['unit'])
            return status, temperature
        else:
            return None, None

    @classmethod
    def tell_the_time(cls,**kwargs):
        """
        Tells ths current time
        """
        now = datetime.now()
        assistant_response('The current time is: {0}:{1}'.format(now.hour, now.minute))

    @classmethod
    def tell_me_about(cls, tag, voice_transcript, skill):
        """
        Tells about something by searching in wikipedia
        :param tag: string (e.g 'about')
        :param voice_transcript: string (e.g 'about google')
        """
        reg_ex = re.search(tag + ' ([a-zA-Z]+)', voice_transcript)
        try:
            if reg_ex:
                topic = reg_ex.group(1)
                response = cls._decoded_wiki_response(topic)
                assistant_response(response)
        except Exception as e:
            logging.debug(e)
            assistant_response(" I can't find on the internet what you want")

    @classmethod
    def _decoded_wiki_response(cls, topic):
        """
        A private method for decoding the wiki response.
        :param topic: string
        :return:
        """
        ny = wikipedia.page(topic)
        data = ny.content[:500].encode('utf-8')
        response = ''
        response += data.decode()
        return response

    @classmethod
    def assistant_check(cls, **kargs):
        """
        Responses that assistant can hear the user.
        """
        assistant_response('Yes, I hear you!')

    @classmethod
    def open_libreoffice_calc(cls, **kargs):
        """
        Opens libreoffice calc application
        """
        # TODO: Refactor all libreoffice methods in one
        subprocess.Popen(['libreoffice', '-calc'], stdout=subprocess.PIPE)
        assistant_response('I opened a new calc document..')

    @classmethod
    def open_libreoffice_writer(cls, **kargs):
        """
        Opens libreoffice writer application
        """
        subprocess.Popen(['libreoffice', '-writer'], stdout=subprocess.PIPE)
        assistant_response('I opened a new writer document..')

    @classmethod
    def open_libreoffice_impress(cls, **kargs):
        """
        Opens libreoffice impress application
        """
        subprocess.Popen(['libreoffice', '-impress'], stdout=subprocess.PIPE)
        assistant_response('I opened a new impress document..')

    @classmethod
    def tell_memory_consumption(**kwargs):
        """
        Responds the memory consumption of the assistant process
        """
        pid = os.getpid()
        py = psutil.Process(pid)
        memoryUse = py.memory_info()[0] / 2. ** 30  # memory use in GB...I think
        assistant_response('I use {} GB..'.format(memoryUse))

    @classmethod
    def open_in_youtube(cls, tag, voice_transcript, **kwargs):
        """
        Open a video in youtube.
        :param tag: string (e.g 'open')
        :param voice_transcript: string (e.g 'open in youtube tdex')
        """
        # TODO:  Replace with YOUTUBE API
        reg_ex = re.search(tag + ' ([a-zA-Z]+)', voice_transcript)
        try:
            if reg_ex:
                search_text = reg_ex.group(1)
                base = "https://www.youtube.com/results?search_query=" + "&orderby=viewCount"
                r = requests.get(base + search_text.replace(' ', '+'))
                page = r.text
                soup = bs(page, 'html.parser')
                vids = soup.findAll('a', attrs={'class': 'yt-uix-tile-link'})
                video = 'https://www.youtube.com' + vids[0]['href']
                subprocess.Popen(["python", "-m", "webbrowser", "-t", video], stdout=subprocess.PIPE)
        except Exception as e:
            logging.debug(e)
            assistant_response("I can't find what do you want in Youtube..")

    @classmethod
    def run_speedtest(cls,**kwargs):
        """
        Run an internet speed test.
        """
        process = subprocess.Popen(["speedtest-cli", "--json"], stdout=subprocess.PIPE)
        out, err = process.communicate()
        if process.returncode:

            decoded_json = cls._decode_json(out)

            ping = decoded_json['ping']
            up_mbps = float(decoded_json['upload']) / 1000000
            down_mbps = float(decoded_json['download']) / 1000000

            assistant_response("Speedtest results:\n"  
                               "The ping is %s ms \n"
                               "The upling is %0.2f Mbps \n"
                               "The downling is %0.2f Mbps" % (ping, up_mbps, down_mbps)
                               )
        else:
            assistant_response("I coudn't run a speedtest")

    @classmethod
    def _decode_json(cls, response_bytes):
        json_response = response_bytes.decode('utf8').replace("'", '"')
        return json.loads(json_response)

    @classmethod
    def spell_a_word(cls, tag, voice_transcript, **kwargs):
        """
        Spell a words letter by letter.
        :param tag: string (e.g 'spell the word')
        :param voice_transcript: string (e.g 'spell the word animal')
        """
        reg_ex = re.search(tag + ' ([a-zA-Z]+)', voice_transcript)
        try:
            if reg_ex:
                search_text = reg_ex.group(1)
                for letter in search_text:
                    assistant_response(letter)
                    time.sleep(2)
        except Exception as e:
            logging.debug(e)
            assistant_response("I can't spell the word")

    @classmethod
    def create_reminder(cls, voice_transcript, **kwargs):
        """
        Creates a simple reminder for the given time interval (seconds or minutes or hours..)
        :param voice_transcript: string (e.g 'Make a reminder in 10 minutes')
        """
        reminder_duration, scheduler_interval = cls._get_reminder_duration_and_time_interval(voice_transcript)

        def reminder():
            assistant_response("Hey, I remind you that now the {0} {1} passed!"
                               .format(reminder_duration, scheduler_interval))
            job.remove()

        try:
            if reminder_duration:
                scheduler = BackgroundScheduler()
                interval = {scheduler_interval: int(reminder_duration)}
                job = scheduler.add_job(reminder, 'interval', **interval)
                assistant_response("I have created a reminder in {0} {1}".format(reminder_duration, scheduler_interval))
                scheduler.start()

        except Exception as e:
            logging.debug(e)
            assistant_response("I can't create a reminder")

    @staticmethod
    def _get_reminder_duration_and_time_interval(voice_transcript):
        """
        Extracts the duration and the time interval from the voice transcript.

        NOTE:
            If there are multiple time intervals, it will extract the first one.
        """
        time_intervals = {
            'seconds': {'variations': ['sec', 'second', 'seconds'],
                        'scheduler_interval': 'seconds'
                        },
            'minutes': {'variations': ['minute', 'minutes'],
                        'scheduler_interval': 'minutes'
                        },
            'hours': {'variations': ['hour', 'hours'],
                      'scheduler_interval': 'hours'
                      },
            'months': {'variations': ['month', 'months'],
                       'scheduler_interval': 'months'
                       },
            'years': {'variations': ['year', 'years'],
                      'scheduler_interval': 'years'
                      },
         }

        for time_interval in time_intervals.values():
            for variation in time_interval['variations']:
                if variation in voice_transcript:
                    print(variation, voice_transcript)
                    reg_ex = re.search('[0-9]', voice_transcript)
                    duration = reg_ex.group(1)
                    return duration, time_interval['scheduler_interval']
