
Session Booking and Scipion pre-processing at SciLifeLab
========================================================

This repository implements a session *Wizard* to address specific needs at the
`Swedish National CryoEM Facility <https://www.scilifelab.se/facilities/cryo-em/>`_
at SciLifelab_ in Stockholm. It contains address two main points:

* Bookkeeping of each microscope session (used for reporting and invoicing)
* Setup for on-the-fly data processing with Scipion

Bookkeeping microscope sessions
-------------------------------
Every time the Session Wizard is started, it will create a new entry in the Sessions database.
The Wizard also read information from our internal Booking System

On-the-fly pre-processing with Scipion
--------------------------------------
This repository contains a more customized "Scipion-Box" wizard for its usage
at the [Swedish National Cryo-EM Facility]().

It setup the data folders for data acquisition and prepare a project for
streaming processing with [Scipion](https://github.com/biocompwebs/scipion/wiki)

.. _SciLifeLab: <http://www.scilifelab.se/>