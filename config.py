

VERSION = '0.3.0'
DATE = '2019-10-07'


VIEW_WIZARD = 'wizardview'

GPU = 'GPU'

# Protocol's contants
MOTIONCORR = "MOTIONCORR"
MOTIONCOR2 = "MOTIONCOR2"
OPTICAL_FLOW = "OPTICAL_FLOW"
SUMMOVIE = "SUMMOVIE"
CTFFIND4 = "CTFFIND4"
GCTF = "GCTF"
EMAIL_NOTIFICATION = "EMAIL_NOTIFICATION"
HTML_REPORT = "HTML_REPORT"
GRIDS = "GRIDS"
CS = "CS"
MAG = "MAG"
VOLTAGE = "VOLTAGE"

# Some related environment variables
DATA_FOLDER = 'DATA_FOLDER'
MOVIES_FOLDER = 'MOVIES_FOLDER'
USER_NAME = 'USER_NAME'
SAMPLE_NAME = 'SAMPLE_NAME'
PROJECT_ID = 'PROJECT_ID'
PROJECT_TYPE = 'PROJECT_TYPE'
PROJECT_FOLDER = 'PROJECT_FOLDER'

SCIPION_PROJECT = 'SCIPION_PROJECT'
FRAMES_RANGE = 'FRAMES_RANGE'
MICROSCOPE = 'MICROSCOPE'
DATA_BACKUP = 'DATA_BACKUP'
PATTERN = 'PATTERN'
HTML_PUBLISH = 'HTML_PUBLISH'
SMTP_SERVER = 'SMTP_SERVER'
SMTP_FROM = 'SMTP_FROM'
SMTP_TO = 'SMTP_TO'

SCIPION_PREPROCESSING = 'Scipion pre-processing'
STREAMING = 'STREAMING'

PROTOCOLS = "Protocols"
MOTION_CORRECTION = 'Motion correction'
CTF_ESTIMATION = 'CTF estimation'
MONITORS = "Monitors"
MICROSCOPE = "Microscope"
CAMERA = "Camera"
MESSAGE = 'Message'

# Define some string constants

LABELS = {
    DATA_FOLDER: "Data folder",
    USER_NAME: "User name",
    SAMPLE_NAME: "Sample name",
    DATA_BACKUP: 'Data Backup Dir',

    PROJECT_TYPE: "Project Type",
    PROJECT_ID: "Project ID",
    PROJECT_FOLDER: "Project folder",
    SCIPION_PROJECT: "Scipion project",
    FRAMES_RANGE: "Frames range",

    # Protocol's contants
    MOTIONCORR: "MotionCorr",
    MOTIONCOR2: "Use MotionCor2",
    OPTICAL_FLOW: "Optical Flow",
    SUMMOVIE: "Summovie (dose compensation)",
    CTFFIND4: "Ctffind4",
    GCTF: "GCtf",
    EMAIL_NOTIFICATION: "Email notification",
    HTML_REPORT: "HTML Report",
}

DEFAULTS = {
    DATA_FOLDER: '/data/staging',
    SCIPION_PREPROCESSING: True,
    STREAMING: True,
    MOTIONCORR: False,
    MOTIONCOR2: True,
    OPTICAL_FLOW: False,
    SUMMOVIE: False,
    CTFFIND4: True,
    GCTF: False,
    # Email notification settings
    EMAIL_NOTIFICATION: False,
    SMTP_SERVER: '',
    SMTP_FROM: '',
    SMTP_TO: '',
    # HTML report settings
    HTML_REPORT: True,
    HTML_PUBLISH: '',
    CS: 2.0,
    MAG: 130000
}

USER_GROUPS = ['cem', 'dbb', 'fac', 'sll']
GROUP_DATA = {
    'cem': 'cem',
    'dbb': 'dbb',
    'fac': 'fac',
    'sll': 'sll'
}

STAFF = ['Marta Carroni -- marta.carroni@scilifelab.se',
         'Julian Conrad -- julian.conrad@scilifelab.se',
         'Karin Wallden -- karin.wallden@scilifelab.se',
         'Dustin Morado -- dustin.morado@scilifelab.se']

# Temporary solution while some users are not registered in the Portal
aa = 'amunts@scilifelab.se'
el = 'erik.lindahl@scilifelab.se'
mo = 'martin.ott@dbb.su.se'
dd = 'ddrew@dbb.su.se'
gu = 'gunnar@dbb.su.se'
pa = 'piaa@dbb.su.se'
pb = 'peterb@dbb.su.se'

PI_MAP = {
    'axelssonlinnea@live.com': aa,
    'Linnea.axelsson@scilifelab.se': aa,
    'vivek.singh@scilifelab.se': aa,

    'bjorn.forsberg@scilifelab.se': el,
    'marie.lycksell@scilifelab.se': el,

    'andreas.carlstrom@dbb.su.se': mo,
    'andreascarlstroem@gmail.com': mo,
    'sorbhi.rathore@dbb.su.se': mo,
    'mikaela@dbb.su.se': mo,

    'pascal.meier@dbb.su.se': dd,
    'yurie.chatzikyriakidou@dbb.su.se': dd,
    'ashutosh.gulati@dbb.su.se': dd,
    'iven.winkelmann@dbb.su.se': dd,

    'bwiseman11@gmail.com': 'hogbom@dbb.su.se',
    'markel.martinez@dbb.su.se': 'stenmark@dbb.su.se',


    # TODO: Register in the Application Portal!!!
    'mara.laguna@scilifelab.se': aa,
    'ane.metola@dbb.su.se': gu,
    'jonathan.davies@dbb.su.se': gu,

    'luka.bacic@icm.uu.se': 'sebastian.deindl@icm.uu.se',



    'patrick.cottilli@scilifelab.se': aa,
    'maximilian.kahle@dbb.su.se': pa,
    'sylwia.krol@dbb.su.se': pb,

    'soneya.majudar@icm.uu.se': 'suparna.sanyal@icm.uu.se',
    'alena.stsiapanava@ki.se': 'luca.jovine@ki.se',

    'hognyi.xu@mmk.su.se': 'hognyi.xu@mmk.su.se',
    'hongyi.xu@mmk.su.se': 'hognyi.xu@mmk.su.se'
}


PROJECT_TYPES = ['National Facility Project',
                 'Internal Project']

# Microscope and camera settings
TITAN = 'Titan Krios'
TALOS = 'Talos Arctica'

MICROSCOPES = [TITAN, TALOS]
MICROSCOPES_ALIAS = {'titan': TITAN, 'talos': TALOS}

K2 = 'K2'
FALCON3 = 'Falcon3'
CAMERAS = [K2, FALCON3]

MIC_CAMERAS = {
    TITAN: [K2, FALCON3],
    TALOS: [FALCON3]
    }

# Configuration dependent on Microscopes
MICROSCOPES_SETTINGS = {
    TITAN: {CS: 2.7, VOLTAGE: 300, GPU: [0]},
    TALOS: {CS: 2.7, VOLTAGE: 200, GPU: [1]}
}

# Configuration dependent on the Camera
CAMERA_SETTINGS = {
    K2: {
        PATTERN: "k2_frames/Images-Disc*/GridSquare_*/Data/FoilHole_*.mrc"
    },
    FALCON3: {
        PATTERN: "k3_frames/Images-Disc*/GridSquare_*/Data/*Fractions.mrc",
    }
}

# Configuration dependent on Microscope-Camera pair
MIC_CAMERAS_SETTINGS = {
    TITAN: {
        K2: {
            MOVIES_FOLDER: DATA_FOLDER
        },
        FALCON3: {
            MOVIES_FOLDER: DATA_FOLDER
        }
    },
    TALOS: {
        FALCON3: {
            MOVIES_FOLDER: DATA_FOLDER
        }
    }
}


# Some data files under the folder 'data'
PORTAL_API = 'portal-api.json'
PORTAL_ORDERS = 'portal-orders.json'
PORTAL_ACCOUNTS = 'portal-accounts.json'

BOOKED_LOGIN_USER = 'booked-user.json'
BOOKED_USERS_LIST = 'booked-users-list.json'
BOOKED_RESERVATIONS = 'booked-reservations.json'

# Small json file with PIs information of the internal users
# in DBB and SciLifeLab
LABS_FILE = 'labs.json'

# The sqlite file where the sessions are stored
SESSIONS_FILE = 'sessions.sqlite'


"""

# Data folder (can be changed per microscope)

# Pattern to be used when importing movies
PATTERN = Images-Disc*/GridSquare_*/Data/FoilHole_*frames.mrc


# ------- MICROSCOPES ----------------
[MICROSCOPE:Talos]
#DATA_FOLDER = /data/talos-falcon2
CS = 2.7
MAG = 72000

[MICROSCOPE:Krios-K2]
PATTERN = k2_frames/Images-Disc*/GridSquare_*/Data/FoilHole_*frames.mrc
CS = 2.7
SCIPION_PROJECT = ${PROJECT_ID}_scipion

[MICROSCOPE:Krios-Falcon2]
#DATA_FOLDER = /data/krios-falcon2
CS = 2.7
"""

import os
# Assume the data folder is in the same place as this script
FILES_DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')


def getDataFile(*paths):
    return os.path.join(FILES_DATA_FOLDER, *paths)