#!/usr/bin/env node
"use strict";
const { createCli } = require("../dist/cli/factory.js");
createCli().parse(process.argv);
