
Session Booking and Scipion pre-processing at SciLifeLab
========================================================

This repository implements a session *Wizard* to address specific needs at the
`Swedish National CryoEM Facility <https://www.scilifelab.se/facilities/cryo-em/>`_
at `SciLifelab <http://www.scilifelab.se/>`_ in Stockholm. It contains address two main points:

* Bookkeeping of each microscope session (used for reporting and invoicing)
* Setup for on-the-fly data processing with Scipion

Bookkeeping microscope sessions
-------------------------------
Every time the Session Wizard is started, it will create a new entry in the Sessions database.
The Wizard read information from our internal `Booking System <https://cryoem-sverige.bookedscheduler.com/>`_ to retrieve which user has the booking for a given microscope during this day. When the booked user is a National User (with a CEMxxxxx project code) the Wizard also fetch information from the `Application Portal <https://cryoem.scilifelab.se/>`_ to grap PI, project description, etc. All these information is stored in the Session database. 

On-the-fly pre-processing with Scipion
--------------------------------------
This repository contains a more customized "Scipion-Box" wizard for its usage
at the [Swedish National Cryo-EM Facility]().

It setup the data folders for data acquisition and prepare a project for
streaming processing with [Scipion](https://github.com/biocompwebs/scipion/wiki)
