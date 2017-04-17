


VIEW_WIZARD = 'wizardview'

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

    PATTERN: "Images-Disc*/GridSquare_*/Data/FoilHole_*frames.mrc",
    CS: 2.0,
    MAG: 130000

}

USER_GROUPS = ['cem', 'dbb', 'fac', 'int']
GROUP_DATA = {
    'cem': 'cem',
    'dbb': 'dbb',
    'fac': 'fac',
    'sll': 'int'
}

STAFF = ['marta.carroni@scilifelab.se',
         'julian.conrad@scilifelab.se']

PROJECT_TYPES = ['National Facility Project',
                 'Internal Project']

# Microscope and camera settings
TITAN = 'Titan Krios'
TALOS = 'Talos Arctica'

MICROSCOPES = [TITAN, TALOS]
MICROSCOPES_ALIAS = {'titan': TITAN, 'talos': TALOS}

K2 = 'K2'
FALCON2 = 'Falcon2'
CAMERAS = [K2, FALCON2]

MIC_CAMERAS = {
    TITAN: [K2, FALCON2],
    TALOS: [FALCON2]
    }

# Configuration dependent on Microscopes
MICROSCOPES_SETTINGS = {
    TITAN: {CS: 2.7, VOLTAGE: 300},
    TALOS: {CS: 2.7, VOLTAGE: 200}
}

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