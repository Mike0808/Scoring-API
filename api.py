#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
import re
from optparse import OptionParser
from weakref import WeakKeyDictionary
from http.server import HTTPServer, BaseHTTPRequestHandler
import scoring

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class CharField(object):
    def __init__(self, required, nullable, **kwargs):
        self.required = required
        self.nullable = nullable
        self.type = str
        self.data = WeakKeyDictionary()

    def __get__(self, instance, cls):
        return self.data.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required")
        else:
            if not isinstance(value, self.type):
                raise TypeError("Must be a ", self.type)
            if not self.nullable and not value:
                raise Exception("Value can't be null")
            else:
                self.data[instance] = value


class ArgumentsField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.arguments = WeakKeyDictionary()
        self.type = dict

    def __get__(self, instance, cls):
        return self.arguments.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        elif value:
            if not isinstance(value, self.type):
                raise TypeError("Must be a ", self.type, "in", str.split(str(self.__class__), ".")[1][:-2])
            if not self.nullable and not value:
                raise Exception("Value can't be null", str.split(str(self.__class__), ".")[1][:-2])
            else:
                self.arguments[instance] = value


class EmailField(CharField):
    def __init__(self, **kwargs):
        self.email_format = r"([-a-zA-Z0-9.`?{}_]+@\w+\.\w+)"
        super().__init__(**kwargs)

    def __set__(self, instance, value):
        super().__set__(instance, value)
        matched = re.match(self.email_format, value)
        if value:
            if matched:
                self.data[instance] = value
            else:
                raise ValueError("Wrong email format", str.split(str(self.__class__), ".")[1][:-2])


class PhoneField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.number = WeakKeyDictionary()

    def __get__(self, instance, cls):
        return self.number.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        else:
            if not self.nullable and not value:
                raise Exception("Value can't be null", str.split(str(self.__class__), ".")[1][:-2])
            elif value:
                pattern = r'^7[0-9]*'
                if re.match(pattern, str(value)) and (len(str(value)) == 11):
                    self.number[instance] = str(value)
                else:
                    raise ValueError("Value must start with 7 and equal 11 digits",
                                 str.split(str(self.__class__), ".")[1][:-2])


class DateField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.bd = WeakKeyDictionary()
        self.type = str

    def __get__(self, instance, cls):
        return self.bd.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        else:
            if not isinstance(value, self.type):
                raise TypeError("Must be a ", self.type)
            if not value and not self.nullable:
                raise Exception("This is the incorrect date string format. It should be DD.MM.YYYY",
                            str.split(str(self.__class__), ".")[1][:-2])
            elif value:
                _format = "%d.%m.%Y"
                value = datetime.datetime.strptime(value, _format)
                self.bd[instance] = value


class BirthDayField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.bd = WeakKeyDictionary()
        self.type = str

    def __get__(self, instance, cls):
        return self.bd.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        else:
            _format = "%d.%m.%Y"
            if not isinstance(value, self.type):
                raise TypeError("Must be a ", self.type)
            if not value and not self.nullable:
                raise Exception("This is the incorrect date string format."
                            " It should be DD.MM.YYYY", str.split(str(self.__class__), ".")[1][:-2])
            elif value:
                value = datetime.datetime.strptime(value, _format)
                older_man = value.year + 70
                today_year = datetime.datetime.today().year
                if older_man < today_year:
                    raise ValueError("You are so old. Your age must be less than 70 ",
                                 str.split(str(self.__class__), ".")[1][:-2])
                self.bd[instance] = value


class GenderField(object):
    def __init__(self, required, nullable):
        self.required = required
        self.nullable = nullable
        self.gen = WeakKeyDictionary()
        self.type = int
        self.gen_list = [0, 1, 2]

    def __get__(self, instance, cls):
        return self.gen.get(instance)

    def __set__(self, instance, value):
        if self.required and not self.nullable and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        else:
            if not self.nullable and not value in self.gen_list:
                raise Exception("Value can't be null", str.split(str(self.__class__), ".")[1][:-2])
            elif value in self.gen_list:
                if not isinstance(value, self.type):
                    raise TypeError("Must be a ", self.type, " or Value of gender must be 0, 1 or 2")
                self.gen[instance] = value
            else:
                raise ValueError("Value must be in " + self.gen_list + " -- " + str.split(str(self.__class__), ".")[1][:-2])


class ClientIDsField(object):
    def __init__(self, required):
        self.required = required
        self.interests = WeakKeyDictionary()
        self.type = list
        self.type_item = int

    def __get__(self, instance, cls):
        return self.interests.get(instance)

    def __set__(self, instance, value):
        if self.required and not value:
            raise Exception("The field is required", str.split(str(self.__class__), ".")[1][:-2])
        else:
            if not isinstance(value, self.type):
                raise TypeError("Must be a ", self.type)
            else:
                for item in value:
                    if not isinstance(item, self.type_item):
                        raise TypeError("List item must be a ", self.type_item, "in",
                                        str.split(str(self.__class__), ".")[1][:-2])
                self.interests[instance] = value


class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=False, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(
            str(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512(str(request.account + request.login + SALT).encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    res = {}
    lst = []
    phone = email = fn = ln = bd = gen = date = ""
    client_ids = []
    response, code = None, None
    meth = MethodRequest()
    score = OnlineScoreRequest()
    interests = ClientsInterestsRequest()
    try:
        meth.login = request['body']['login']
        meth.account = request['body']['account']
        meth.token = request['body']['token']
        meth.arguments = request['body']['arguments']
        meth.method = request['body']['method']
        b = check_auth(meth)
        if not b:
            return {"code": 403, "error": "Forbidden"}, FORBIDDEN, lst
        if meth.method == "online_score":
            dict_arg = meth.arguments
            score.email = dict_arg['email'] if 'email' in dict_arg.keys() else ""
            score.phone = dict_arg['phone'] if 'phone' in dict_arg.keys() else ""
            score.last_name = dict_arg['last_name'] if 'last_name' in dict_arg.keys() else ""
            score.first_name = dict_arg['first_name'] if 'first_name' in dict_arg.keys() else ""
            score.gender = dict_arg['gender'] if 'gender' in dict_arg.keys() else 0
            score.birthday = dict_arg['birthday'] if 'birthday' in dict_arg.keys() else ""
        elif meth.method == "clients_interests":
            dict_arg = meth.arguments
            interests.client_ids = dict_arg['client_ids'] if 'client_ids' in dict_arg.keys() else []
            interests.date = dict_arg['date'] if 'date' in dict_arg.keys() else ""
        else:
            raise Exception("No method found")
        for k, v in dict_arg.items():
            if k == 'phone' and v:
                phone = v
                lst.append(k)
            elif k == 'email' and v:
                email = v
                lst.append(k)
            elif k == 'first_name' and v:
                fn = v
                lst.append(k)
            elif k == 'last_name' and v:
                ln = v
                lst.append(k)
            elif k == 'birthday' and v:
                bd = v
                lst.append(k)
            elif k == 'gender' and str(v):
                gen = str(v)
                lst.append(k)
            elif k == 'client_ids' and v:
                client_ids = v
                lst = len(v)
            elif k == 'date' and v:
                date = v
            else:
                logging.error("You've not pair")
        if (phone and email) or (fn and ln) or (gen and bd):
            if meth.login == ADMIN_LOGIN:
                res['score'] = 42.0
            else:
                res['score'] = scoring.get_score(store, phone, email, bd, gen, fn, ln)
        elif client_ids:
            for item in client_ids:
                res["client_id" + str(item)] = scoring.get_interests(store, item)
        else:
            raise Exception("Invalid request: ", INVALID_REQUEST, lst)
    except Exception as e:
        return {"code": 422, "error": e}, INVALID_REQUEST, lst
    return res, OK, lst


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code, context['has'] = self.router[path]({"body": request, "headers": self.headers},
                                                                       context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(b'```\n')
        self.wfile.write(b'```\n')
        self.wfile.write(json.dumps(r).encode(encoding='utf_8'))
        self.wfile.write(b'\n```')
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
