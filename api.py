#!/usr/bin/env python
# -*- coding: utf-8 -*-
# https://pastebin.com/WpDpDfeX
import abc
import json
import datetime
import logging
import hashlib
import uuid
import re
from optparse import OptionParser
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


class Field(object):
    def __init__(self, nullable=False, required=False):
        self.nullable = nullable
        self.required = required

    def parse_validate(self, value):
        return value


class CharField(Field):
    def parse_validate(self, value):
        if isinstance(value, str):
            return value
        raise ValueError("value is not a string")


class ArgumentsField(Field):
    def parse_validate(self, value):
        if isinstance(value, dict):
            return value
        raise ValueError("value is not a dictionary")


class EmailField(CharField):
    def parse_validate(self, value):
        value = super().parse_validate(value)
        if "@" in value:
            return value
        raise ValueError("value is not an email")


class PhoneField(Field):
    def parse_validate(self, value):  # code here
        pattern = r'^7[0-9]*'
        if isinstance(value, str) or isinstance(value, int):
            if re.match(pattern, str(value)) and (len(str(value)) == 11):
                return value
            raise ValueError("Value is not a phone number. Must start with 7 and equal 11 digits")


class DateField(Field):
    def parse_validate(self, value):  # code here
        if isinstance(value, str):
            _format = "%d.%m.%Y"
            value = datetime.datetime.strptime(value, _format)
            return value
        raise ValueError("This is the incorrect date string format. It should be DD.MM.YYYY")


class BirthDayField(DateField):
    def parse_validate(self, value):  # code here
        _format = "%d.%m.%Y"
        if isinstance(value, str):
            value = datetime.datetime.strptime(value, _format)
            older_man = value.year + 70
            today_year = datetime.datetime.today().year
            if older_man < today_year:
                raise ValueError("You are so old. Your age must be less than 70 ",
                                 str.split(str(self.__class__), ".")[1][:-2])
            return value
        raise ValueError("This is the incorrect date string format."
                         " It should be DD.MM.YYYY")


class GenderField(Field):
    def parse_validate(self, value):  # code here
        self.gen_list = [0, 1, 2]
        if isinstance(value, int) and value in self.gen_list:
            return str(value)
        raise ValueError(
            "Value must be in " + str(self.gen_list))


class ClientIDsField(Field):
    def parse_validate(self, value):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, int):
                    return value
                raise ValueError("List item must be an int")
        raise ValueError("Field must be a list type. ")


class RequestHandler(object):
    def validate_handle(self, request, arguments, ctx, store):
        if not arguments.is_valid():
            return arguments.errfmt(), INVALID_REQUEST
        return self.handle(request, arguments, ctx, store)

    def handle(self, request, arguments, ctx):
        return {}, OK


class RequestMeta(type):
    def __new__(mcs, name, bases, attrs):
        field_list = []
        for k, v in attrs.items():
            if isinstance(v, Field):
                v.name = k
                field_list.append(v)
        cls = super().__new__(mcs, name, bases, attrs)
        cls.fields = field_list
        return cls


class Request(object, metaclass=RequestMeta):
    def __init__(self, request):
        self.errors = []
        self.request = request
        self.is_cleaned = False

    def clean(self):
        for f in self.fields:  # code here
            try:
                name = f.name
                req = f.required
                has_name = name in self.request
                if req and has_name:
                    if not self.request[name] and not f.nullable:
                        self.errors.append("Error in " + str(name) + ". Required field must be non-nullable ")
                elif req and not has_name:
                    self.errors.append("Error in " + str(name) + ". This is Required field.")
                if has_name:
                    parse = f.parse_validate(self.request[name])
                    setattr(self, name, parse)
                else:
                    setattr(self, name, "")
            except ValueError as e:
                self.errors.append("Error in validate field: " + str(name) + ". " + str(e))

    def is_valid(self):
        if not self.is_cleaned:
            self.clean()
        return not self.errors

    def errfmt(self):
        return ", ".join(self.errors)


class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class ClientsInterestsHandler(RequestHandler):
    request_type = ClientsInterestsRequest

    def handle(self, request, arguments, ctx, store):
        ctx["nclients"] = len(arguments.client_ids)
        return {cid: scoring.get_interests(store, cid) for cid in arguments.client_ids}, OK


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def is_valid(self):
        default_valid = super().is_valid()
        if not default_valid:
            return default_valid
        # code here
        if (self.first_name and self.last_name) or (self.phone and self.email) or (self.gender and self.birthday):
            return not self.errfmt()
        else:
            self.errors.append("Error in validate field")
        return not self.errfmt()




class OnlineScoreHandler(RequestHandler):
    request_type = OnlineScoreRequest
    def handle(self, request, arguments, ctx, store):
        score = scoring.get_score(store,
                                  arguments.phone, arguments.email,
                                  arguments.birthday, arguments.gender,
                                  arguments.first_name, arguments.last_name)
        arg = []
        if request.login == ADMIN_LOGIN:
            return {"score": 42}, OK
        for f in self.request_type.fields:
            if getattr(arguments, f.name):
                arg.append(f.name)
        ctx["has"] = arg

        return {"score": score}, OK


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
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
    methods_map = {
        "online_score": OnlineScoreHandler,
        "clients_interests": ClientsInterestsHandler,
    }
    method_request = MethodRequest(request["body"])
    if not method_request.is_valid():
        return method_request.errfmt(), INVALID_REQUEST
    if not check_auth(method_request):
        return None, FORBIDDEN
    handler_cls = methods_map.get(method_request.method)
    if not handler_cls:
        return "Method Not Found", NOT_FOUND
    response, code = handler_cls().validate_handle(method_request,
                                                   handler_cls.request_type(method_request.arguments),
                                                   ctx, store)
    return response, code


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
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
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
            # @TODO: return errors as array
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode(encoding='utf_8'))
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
