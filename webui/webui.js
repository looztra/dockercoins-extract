var express = require('express');
var app = express();
var redis = require('redis');

var redisHost = process.env.DOCKERCOINS_REDIS_HOST;
var redisPort = process.env.DOCKERCOINS_REDIS_PORT;

console.info("redisHost from env : " + redisHost);
console.info("redisPort from env : " + redisPort);

if (typeof redisHost == 'undefined') {
    console.info("using default value for 'redisHost'")
    redisHost = 'redis';
}

if (typeof redisPort == 'undefined') {
    console.info("using default value for 'redisPort'")
    redisPort = 6379;
}

var client = redis.createClient(redisPort, redisHost);
client.on("error", function (err) {
    console.error("Redis error", err);
});

app.get('/', function (req, res) {
    res.redirect('/index.html');
});

app.get('/json', function (req, res) {
    client.hlen('wallet', function (err, coins) {
        client.get('hashes', function (err, hashes) {
            var now = Date.now() / 1000;
            res.json({
                coins: coins,
                hashes: hashes,
                now: now
            });
        });
    });
});

app.use(express.static('files'));

var server = app.listen(80, function () {
    console.log('WEBUI running on port 80');
});

