# Glossary

Every technical word used in the book, in alphabetical order. The section in brackets is where the idea is first explained.

Age assurance
:   Any method of establishing someone's age with some level of confidence. The umbrella term for verification, estimation and inference. (§1.5)

Age estimation
:   Guessing age from a physical characteristic, usually the face. Fast and private, but it always carries some error. (§1.5)

Age inference
:   Deducing age from other facts, such as holding a credit card. (§1.5)

Age verification
:   Establishing age from an authoritative source, such as an ID document or a digital-ID app. (§1.5)

API
:   *Application Programming Interface.* A menu of requests one program offers to other programs. Each request it accepts is an **endpoint**. (§0.11)

Argument
:   A value handed to a function or a command. In `python build.py --strict`, `--strict` is an argument. (Part X)

Audit log
:   A permanent, ordered record of important events (who changed what, when). Ours is *tamper-evident*: each entry includes a fingerprint of the previous one. (§3.3)

Backend
:   The programs that run on servers, out of the user's sight. (§0.10)

Biometric data
:   Information about a person's body, such as their face. (§1.11)

Bit, byte
:   A bit is a single 0 or 1. A byte is 8 bits, enough for a number from 0 to 255. (§0.1)

Buffer / challenge age
:   An extra margin above the legal age. For example, "pass only if the estimate is 25 or more, for a legal age of 18". (§1.8)

Certificate
:   A digital document, signed by a trusted organisation, proving a server's identity for HTTPS. (§0.9)

Client
:   A program that asks a server for something — for example, a web browser. (§0.7)

Clopper–Pearson bound
:   A method for working out, from a test result like "6 out of 600", the worst plausible true rate at a chosen confidence level. (§3.3)

Code / source code
:   The human-readable instructions of a program, written in a programming language. (§0.3)

Commit
:   A saved snapshot of a project in Git, with a message explaining the change. (§0.15)

Compiler
:   A program that translates a whole program into machine code before it runs. (§0.4)

Container
:   A running copy of a Docker image. (§0.14)

Coverage
:   In this book: the share of a file's non-blank lines that have an explanation. (Part X)

Database
:   A program that stores data permanently and answers questions about it quickly and safely. (§0.12)

Dataclass
:   A Python shortcut for defining a class that mainly holds data. (Part X)

Deploy
:   To copy a program onto a server and start it there. (§0.13)

Dictionary (dict)
:   A Python collection of labelled values, looked up by key: `{"title": "Dwarpal"}`. (Part X)

DNS
:   *Domain Name System.* The internet's phone book, turning names into IP addresses. (§0.6)

Docker / image / volume
:   Docker packs a program with everything it needs into an **image**. A **volume** is a folder that survives when containers are thrown away. (§0.14)

Domain
:   A human-friendly internet name, such as `dwarpal.example`. (§0.13)

Encoding
:   The agreement that maps characters to numbers. We always use UTF-8. (§0.2)

Endpoint
:   One specific request an API accepts, identified by a method and a path, such as `POST /v1/verification-sessions`. (§0.11)

Extension (file)
:   The letters after the last dot in a file name, such as `.py`, hinting at the kind of file. (§0.2)

Fail closed
:   When something goes wrong, the system chooses the *safe* answer ("retry" or "step-up"), never "pass". (§1.13)

False-adult rate
:   The share of children near the age limit whom the system wrongly lets through. Our most important safety number. (§1.7)

Fingerprint (hash)
:   A short code computed from a file's contents. Change one character and the fingerprint changes completely. (Part X)

Frontend
:   Everything that runs in the user's browser. (§0.10)

Function
:   A named, reusable block of code that takes inputs and gives back a result. (Part X)

Git, GitHub
:   Git records a project's history as commits. GitHub stores Git projects online. (§0.15)

GPU
:   *Graphics Processing Unit.* A chip that performs thousands of calculations at once — ideal for AI. (§0.1)

Hosting
:   Renting computers in a data centre to run your website. (§0.13)

HTML, CSS, JavaScript
:   The skeleton, the clothes and the muscles of a web page. (§0.10)

HTTP, HTTPS
:   The protocol browsers and servers use to talk. HTTPS is HTTP inside TLS encryption. (§0.8, §0.9)

Injection attack
:   Bypassing the camera completely, for example with software that pretends to be a camera. (§1.10)

Interpreter
:   A program that runs code by reading it line by line. (§0.4)

IP address, port
:   An IP address identifies a computer on a network (the building). A port identifies one program on it (the flat). (§0.6)

JSON
:   A plain-text format for structured data, with six kinds of value. (§0.11)

Library / package
:   Code written by someone else that you can reuse. (§0.17)

Licence
:   The legal rules for what you may do with someone else's code, model or data. (§0.16)

Liveness
:   Evidence that a real, live person is in front of the camera at that moment. (§1.10)

localhost
:   A name that always means "this same computer". (§0.6)

Lockfile
:   An automatically generated list of the exact version of every library a project uses. (§0.17)

Markdown
:   A simple way of writing formatted text with symbols like `#` for headings and `**` for bold. This book is written in it. (Part X)

Method (HTTP)
:   The kind of action an HTTP request asks for: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. (§0.8)

Model (AI)
:   A mathematical function with many adjustable numbers (parameters), tuned from examples so that it produces useful answers. (§1.6, Part 2)

Mojibake
:   Garbled text caused by reading a file with the wrong encoding. (§0.2)

Pinning
:   Recording the exact version of a library, so the project builds identically everywhere. (§0.17)

Pixel
:   One dot of a digital image, stored as red, green and blue numbers. (§0.1)

Presentation attack
:   Showing the camera something that isn't a live face: a photo, a screen, a mask. (§1.10)

Program
:   A set of instructions for a computer. (§0.3)

Protocol
:   An agreed set of rules for how messages are formatted and exchanged. (§0.8)

Proxy (attack)
:   An adult doing the age check on a child's behalf. (§1.10)

Regular expression (regex)
:   A tiny pattern language for finding text, such as "two @ signs followed by a number". (Part X)

Relying party
:   The website or app that relies on our age answer. (§3.3)

Request / response
:   One message from a client, and the server's reply. (§0.8)

Risk budget
:   The maximum share of dangerous mistakes a policy accepts, for example "at most 2 % of 13–17-year-olds may pass". (§3.3)

Server
:   A program (or the computer running it) that waits for requests and answers them. (§0.7)

Shell / terminal
:   The window and program where you type commands. (§0.5)

Signed token
:   A small digital message sealed with a private key, so anyone with the public key can check that it is genuine and unchanged. (§3.3)

Status code
:   The three-digit number at the start of an HTTP response: 2xx success, 4xx client error, 5xx server error. (§0.8)

Step-up
:   Moving to a stronger age-check method when the quick one is unsure. (§1.9)

Table (database)
:   Rows (things) and columns (their properties), like a spreadsheet. (§0.12)

Template
:   A file with blanks (here written like `{{TITLE}}`) that a program fills in. (Part X)

TLS
:   *Transport Layer Security.* The encryption behind HTTPS. (§0.9)

Transaction
:   A group of database changes that either all happen or none happen. (§0.12)

UTF-8
:   The universal text encoding, able to store every character in every language. (§0.2)

Version
:   A label like `3.11.1` (*major.minor.patch*) identifying one release of a library. (§0.17)

Virtual environment (venv)
:   A private folder holding a specific Python and specific libraries for one project, so projects don't interfere with each other. (Part X)

Walkthrough
:   In this book: a file that explains another file line by line. (Part X)

Waterfall
:   Trying the quickest, most private age check first, and moving to stronger methods only when needed. (§1.9)
