# sharesfor
---
sharesfor is an open source messaging and collaboration platform, that features simple integration capabilities with your existing applications. 
sharesfor can relate to objects in your existing application and provide message threads related to that object -and others that may be co-related- thereby sharing and collecting information on it.

Objects can for instance be the accounts, contacts, projects, etc. in your CRM; the courses, lectures, subjects, classes, etc. on your Learning Management Sytem;  or any other item in any of your applications.

sharesfor provides a familiar real time messaging interface so that users provide personal/corporate memory on those objects by creating and populating message threads. It provides a real time messaging mechanism, so users can chat on the objects while creating valuable information for their organization, company, community, etc. A simple demo is available  [here](https://s4s4demo.pluralist.team) which presents some sample objects that link to sharesfor where you can create and append to message threads on them. 

sharesfor is activated through a POST request with the following parameters:
{userid, username, email, otype, oid}
which corresponds to user information (userid, username, email) and object information (otype: object type; oid: object id). 

See integration.md for integrating your application with sharesfor and installation.md for sharesfor installation instructions.


### Technology Stack
-- Backend: Python Flask
-- Database: MongoDB
-- Real-Time Communication: Socket.IO


### Contributing
Contributions are welcome! To contribute:
	Fork the repository.
	Create a new branch for your feature or bug fix.
	Submit a pull request.

### License
This project is licensed under the MIT License. See the LICENSE file for details.

### Contact

For questions or support, please reach out to:

Email: ceskinat@gmail.com



