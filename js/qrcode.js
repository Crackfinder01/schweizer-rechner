/*
 * Minimal QR Code encoder (ISO/IEC 18004), byte mode only, written for this project.
 * - Fixed error correction level (no automatic "boost"): the Swiss QR-bill requires level M.
 * - Picks the smallest version that fits, then the mask with the lowest penalty score.
 * No dependency, no network. Works in the browser (window.QRCode) and in Node (module.exports).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.QRCode = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Error correction levels: index into the tables below + 2-bit format code.
  var ECL = {
    L: { ordinal: 0, formatBits: 1 },
    M: { ordinal: 1, formatBits: 0 },
    Q: { ordinal: 2, formatBits: 3 },
    H: { ordinal: 3, formatBits: 2 }
  };

  // ISO/IEC 18004 Table 9: error correction codewords per block, index = version (0 unused).
  var ECC_CODEWORDS_PER_BLOCK = [
    [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
  ];
  // Number of error correction blocks, index = version (0 unused).
  var NUM_ERROR_CORRECTION_BLOCKS = [
    [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81]
  ];

  function getBit(x, i) { return ((x >>> i) & 1) !== 0; }

  /** UTF-8 bytes of a string. */
  function utf8(str) {
    var s = String(str);
    if (typeof TextEncoder !== 'undefined') return Array.prototype.slice.call(new TextEncoder().encode(s));
    var bin = unescape(encodeURIComponent(s));
    var out = [];
    for (var i = 0; i < bin.length; i++) out.push(bin.charCodeAt(i));
    return out;
  }

  /** Number of data + ECC bits available in a version (all modules minus function patterns). */
  function numRawDataModules(ver) {
    var result = (16 * ver + 128) * ver + 64;
    if (ver >= 2) {
      var numAlign = Math.floor(ver / 7) + 2;
      result -= (25 * numAlign - 10) * numAlign - 55;
      if (ver >= 7) result -= 36;
    }
    return result;
  }

  function numDataCodewords(ver, ecl) {
    return Math.floor(numRawDataModules(ver) / 8) -
      ECC_CODEWORDS_PER_BLOCK[ecl.ordinal][ver] * NUM_ERROR_CORRECTION_BLOCKS[ecl.ordinal][ver];
  }

  /** Max number of bytes in byte mode for a version and level. */
  function byteCapacity(ver, eclName) {
    var ecl = ECL[eclName];
    var ccBits = ver <= 9 ? 8 : 16;
    return Math.floor((numDataCodewords(ver, ecl) * 8 - 4 - ccBits) / 8);
  }

  // ---------- Reed-Solomon over GF(2^8), polynomial 0x11D ----------
  function gfMul(x, y) {
    var z = 0;
    for (var i = 7; i >= 0; i--) {
      z = (z << 1) ^ ((z >>> 7) * 0x11D);
      z ^= ((y >>> i) & 1) * x;
    }
    return z & 0xFF;
  }

  function rsDivisor(degree) {
    var result = [];
    for (var i = 0; i < degree - 1; i++) result.push(0);
    result.push(1);
    var root = 1;
    for (var k = 0; k < degree; k++) {
      for (var j = 0; j < result.length; j++) {
        result[j] = gfMul(result[j], root);
        if (j + 1 < result.length) result[j] ^= result[j + 1];
      }
      root = gfMul(root, 0x02);
    }
    return result;
  }

  function rsRemainder(data, divisor) {
    var result = divisor.map(function () { return 0; });
    data.forEach(function (b) {
      var factor = b ^ result.shift();
      result.push(0);
      divisor.forEach(function (coef, i) { result[i] ^= gfMul(coef, factor); });
    });
    return result;
  }

  /** Split data into blocks, add ECC, interleave. */
  function addEccAndInterleave(data, ver, ecl) {
    var numBlocks = NUM_ERROR_CORRECTION_BLOCKS[ecl.ordinal][ver];
    var blockEccLen = ECC_CODEWORDS_PER_BLOCK[ecl.ordinal][ver];
    var rawCodewords = Math.floor(numRawDataModules(ver) / 8);
    var numShortBlocks = numBlocks - rawCodewords % numBlocks;
    var shortBlockLen = Math.floor(rawCodewords / numBlocks);
    var blocks = [];
    var divisor = rsDivisor(blockEccLen);
    for (var i = 0, k = 0; i < numBlocks; i++) {
      var datLen = shortBlockLen - blockEccLen + (i < numShortBlocks ? 0 : 1);
      var dat = data.slice(k, k + datLen);
      k += datLen;
      var ecc = rsRemainder(dat, divisor);
      if (i < numShortBlocks) dat.push(0); // placeholder, skipped below
      blocks.push(dat.concat(ecc));
    }
    var result = [];
    for (var c = 0; c < blocks[0].length; c++) {
      for (var b = 0; b < blocks.length; b++) {
        if (c !== shortBlockLen - blockEccLen || b >= numShortBlocks) result.push(blocks[b][c]);
      }
    }
    return result;
  }

  // ---------- matrix construction ----------
  function Matrix(ver) {
    this.version = ver;
    this.size = ver * 4 + 17;
    this.modules = [];
    this.isFunction = [];
    for (var y = 0; y < this.size; y++) {
      this.modules.push(new Array(this.size).fill(false));
      this.isFunction.push(new Array(this.size).fill(false));
    }
  }

  Matrix.prototype.setFn = function (x, y, dark) {
    this.modules[y][x] = dark;
    this.isFunction[y][x] = true;
  };

  Matrix.prototype.alignmentPositions = function () {
    var ver = this.version;
    if (ver === 1) return [];
    var numAlign = Math.floor(ver / 7) + 2;
    var step = ver === 32 ? 26 : Math.ceil((ver * 4 + 4) / (numAlign * 2 - 2)) * 2;
    var result = [6];
    for (var pos = this.size - 7; result.length < numAlign; pos -= step) result.splice(1, 0, pos);
    return result;
  };

  Matrix.prototype.drawFinder = function (x, y) {
    for (var dy = -4; dy <= 4; dy++) {
      for (var dx = -4; dx <= 4; dx++) {
        var dist = Math.max(Math.abs(dx), Math.abs(dy));
        var xx = x + dx;
        var yy = y + dy;
        if (xx >= 0 && xx < this.size && yy >= 0 && yy < this.size) this.setFn(xx, yy, dist !== 2 && dist !== 4);
      }
    }
  };

  Matrix.prototype.drawAlignment = function (x, y) {
    for (var dy = -2; dy <= 2; dy++) {
      for (var dx = -2; dx <= 2; dx++) this.setFn(x + dx, y + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
    }
  };

  Matrix.prototype.drawFormatBits = function (ecl, mask) {
    var data = (ecl.formatBits << 3) | mask;
    var rem = data;
    for (var i = 0; i < 10; i++) rem = (rem << 1) ^ ((rem >>> 9) * 0x537);
    var bits = ((data << 10) | rem) ^ 0x5412;
    var size = this.size;
    for (i = 0; i <= 5; i++) this.setFn(8, i, getBit(bits, i));
    this.setFn(8, 7, getBit(bits, 6));
    this.setFn(8, 8, getBit(bits, 7));
    this.setFn(7, 8, getBit(bits, 8));
    for (i = 9; i < 15; i++) this.setFn(14 - i, 8, getBit(bits, i));
    for (i = 0; i < 8; i++) this.setFn(size - 1 - i, 8, getBit(bits, i));
    for (i = 8; i < 15; i++) this.setFn(8, size - 15 + i, getBit(bits, i));
    this.setFn(8, size - 8, true); // dark module
    return bits;
  };

  Matrix.prototype.drawVersion = function () {
    if (this.version < 7) return;
    var rem = this.version;
    for (var i = 0; i < 12; i++) rem = (rem << 1) ^ ((rem >>> 11) * 0x1F25);
    var bits = (this.version << 12) | rem;
    for (i = 0; i < 18; i++) {
      var bit = getBit(bits, i);
      var a = this.size - 11 + (i % 3);
      var b = Math.floor(i / 3);
      this.setFn(a, b, bit);
      this.setFn(b, a, bit);
    }
  };

  Matrix.prototype.drawFunctionPatterns = function (ecl) {
    var size = this.size;
    for (var i = 0; i < size; i++) {
      this.setFn(6, i, i % 2 === 0);
      this.setFn(i, 6, i % 2 === 0);
    }
    this.drawFinder(3, 3);
    this.drawFinder(size - 4, 3);
    this.drawFinder(3, size - 4);
    var pos = this.alignmentPositions();
    var n = pos.length;
    for (var a = 0; a < n; a++) {
      for (var b = 0; b < n; b++) {
        if ((a === 0 && b === 0) || (a === 0 && b === n - 1) || (a === n - 1 && b === 0)) continue;
        this.drawAlignment(pos[a], pos[b]);
      }
    }
    this.drawFormatBits(ecl, 0); // reserve area, real bits drawn after masking
    this.drawVersion();
  };

  Matrix.prototype.drawCodewords = function (data) {
    var size = this.size;
    var i = 0;
    for (var right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (var vert = 0; vert < size; vert++) {
        for (var j = 0; j < 2; j++) {
          var x = right - j;
          var upward = ((right + 1) & 2) === 0;
          var y = upward ? size - 1 - vert : vert;
          if (!this.isFunction[y][x] && i < data.length * 8) {
            this.modules[y][x] = getBit(data[i >>> 3], 7 - (i & 7));
            i++;
          }
        }
      }
    }
  };

  function maskBit(mask, x, y) {
    switch (mask) {
      case 0: return (x + y) % 2 === 0;
      case 1: return y % 2 === 0;
      case 2: return x % 3 === 0;
      case 3: return (x + y) % 3 === 0;
      case 4: return (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0;
      case 5: return (x * y) % 2 + (x * y) % 3 === 0;
      case 6: return ((x * y) % 2 + (x * y) % 3) % 2 === 0;
      case 7: return ((x + y) % 2 + (x * y) % 3) % 2 === 0;
    }
    throw new Error('mask');
  }

  Matrix.prototype.applyMask = function (mask) {
    for (var y = 0; y < this.size; y++) {
      for (var x = 0; x < this.size; x++) {
        if (!this.isFunction[y][x] && maskBit(mask, x, y)) this.modules[y][x] = !this.modules[y][x];
      }
    }
  };

  /** Penalty score (ISO 18004 section 7.8.3), used only to choose a good mask. */
  Matrix.prototype.penalty = function () {
    var size = this.size;
    var m = this.modules;
    var score = 0;
    var x, y, run, color;
    function cell(xx, yy, vertical) { return vertical ? m[xx][yy] : m[yy][xx]; }
    for (var pass = 0; pass < 2; pass++) {
      var vertical = pass === 1;
      for (y = 0; y < size; y++) {
        run = 0; color = null;
        for (x = 0; x < size; x++) {
          var c = cell(x, y, vertical);
          if (c === color) {
            run++;
            if (run === 5) score += 3;
            else if (run > 5) score += 1;
          } else { color = c; run = 1; }
        }
        // finder-like pattern 1:1:3:1:1 with 4 light modules on one side
        for (x = 0; x + 10 < size; x++) {
          var p = [];
          for (var k = 0; k < 11; k++) p.push(cell(x + k, y, vertical) ? 1 : 0);
          var s = p.join('');
          if (s === '10111010000' || s === '00001011101') score += 40;
        }
      }
    }
    for (y = 0; y < size - 1; y++) {
      for (x = 0; x < size - 1; x++) {
        var v = m[y][x];
        if (v === m[y][x + 1] && v === m[y + 1][x] && v === m[y + 1][x + 1]) score += 3;
      }
    }
    var dark = 0;
    for (y = 0; y < size; y++) for (x = 0; x < size; x++) if (m[y][x]) dark++;
    var total = size * size;
    var k2 = Math.ceil(Math.abs(dark * 20 - total * 10) / total) - 1;
    score += Math.max(0, k2) * 10;
    return score;
  };

  /**
   * Encode text (UTF-8, byte mode).
   * options: { ecl: 'L'|'M'|'Q'|'H' (default 'M'), minVersion, maxVersion, mask (0-7, default auto) }
   * Returns { version, size, ecl, mask, modules: boolean[][] } (modules[y][x], true = dark).
   */
  function encode(text, options) {
    var opts = options || {};
    var eclName = opts.ecl || 'M';
    var ecl = ECL[eclName];
    if (!ecl) throw new Error('Invalid error correction level');
    var bytes = utf8(text);
    var minV = opts.minVersion || 1;
    var maxV = opts.maxVersion || 40;
    var ver;
    for (ver = minV; ver <= maxV; ver++) {
      if (bytes.length <= byteCapacity(ver, eclName)) break;
    }
    if (ver > maxV) throw new Error('Data too long for a QR code');

    // bit stream: mode indicator 0100 (byte), character count, data
    var bits = [];
    function push(val, len) { for (var i = len - 1; i >= 0; i--) bits.push((val >>> i) & 1); }
    push(4, 4);
    push(bytes.length, ver <= 9 ? 8 : 16);
    bytes.forEach(function (b) { push(b, 8); });
    var capacityBits = numDataCodewords(ver, ecl) * 8;
    push(0, Math.min(4, capacityBits - bits.length)); // terminator
    push(0, (8 - bits.length % 8) % 8);
    for (var pad = 0xEC; bits.length < capacityBits; pad ^= 0xEC ^ 0x11) push(pad, 8);
    var data = [];
    for (var i = 0; i < bits.length; i += 8) {
      var byte = 0;
      for (var j = 0; j < 8; j++) byte = (byte << 1) | bits[i + j];
      data.push(byte);
    }

    var codewords = addEccAndInterleave(data, ver, ecl);
    var mx = new Matrix(ver);
    mx.drawFunctionPatterns(ecl);
    mx.drawCodewords(codewords);

    var mask = opts.mask;
    if (mask === undefined || mask === null) {
      var best = Infinity;
      for (var mk = 0; mk < 8; mk++) {
        mx.applyMask(mk);
        mx.drawFormatBits(ecl, mk);
        var pen = mx.penalty();
        if (pen < best) { best = pen; mask = mk; }
        mx.applyMask(mk); // undo (XOR)
      }
    }
    mx.applyMask(mask);
    mx.drawFormatBits(ecl, mask);
    return { version: ver, size: mx.size, ecl: eclName, mask: mask, modules: mx.modules };
  }

  /** SVG path ("d" attribute) of the dark modules, 1 unit = 1 module, no quiet zone. */
  function toPath(qr) {
    var d = [];
    for (var y = 0; y < qr.size; y++) {
      var x = 0;
      while (x < qr.size) {
        if (qr.modules[y][x]) {
          var start = x;
          while (x < qr.size && qr.modules[y][x]) x++;
          d.push('M' + start + ' ' + y + 'h' + (x - start) + 'v1h-' + (x - start) + 'z');
        } else {
          x++;
        }
      }
    }
    return d.join('');
  }

  return {
    encode: encode,
    toPath: toPath,
    byteCapacity: byteCapacity,
    utf8: utf8
  };
});
