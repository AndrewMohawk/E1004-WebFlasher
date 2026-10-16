# E1004 Web Flasher

A static Web Serial installer for the [NYTDisplay general-edition firmware](https://github.com/AndrewMohawk/NYTDisplay) on the Seeed reTerminal E1004. It includes a prepared factory image and also accepts a local merged ESP32-S3 `.bin` file. Local files stay in the browser.

**[Open the HTTPS web flasher](https://andrewmohawk.github.io/E1004-WebFlasher/)**

The prepared image is an **experimental build** of [firmware commit `084c946`](https://github.com/AndrewMohawk/NYTDisplay/commit/084c946e38cc3dd3026a0c3b61042b3434c3050c). It built and passed host checks, but this edition has not yet been flashed and tested on a physical E1004.

## Use

Serve this directory over HTTPS, or run `python3 -m http.server 8000` and open `http://localhost:8000`. Use desktop Chrome or Edge and a USB-C data cable. Confirm the device is a **reTerminal E1004** before selecting its serial port. The installer can offer to erase existing device settings during a new installation.

Choose the prepared general edition or select a local merged image for offset zero, then click **Connect & flash**. An application-only `firmware.bin` is not suitable for the local file option. The page checks only the image marker and size; it cannot establish that a custom image matches your board.

This is a static site: no server-side upload, account, or deployment-specific configuration is required. The browser flasher uses the pinned [ESP Web Tools 10.4.0](https://github.com/esphome/esp-web-tools) package.

## Regenerate the prepared image

Build the [general-edition source](https://github.com/AndrewMohawk/NYTDisplay) with PlatformIO. Map your PlatformIO package path out of compiler strings before generating a public image. With the usual package location:

```sh
PIO_PACKAGES="$HOME/.platformio/packages"
PLATFORMIO_BUILD_FLAGS="-D BOARD_HAS_PSRAM -ffile-prefix-map=$PIO_PACKAGES=platformio" \
  pio run -d PATH_TO_FIRMWARE -e reterminal_e1004
```

Then run:

```sh
python3 tools/build_release.py \
  --build-dir PATH_TO_FIRMWARE/.pio/build/reterminal_e1004 \
  --version 0.1.0+084c946
```

The script merges the ESP32-S3 bootloader, partition table, OTA initialization image, and application at offsets `0x0`, `0x8000`, `0xe000`, and `0x10000`. It writes `firmware/factory.bin` and `firmware/manifest.json`. If PlatformIO uses a custom packages directory, set `PLATFORMIO_PACKAGES_DIR` or pass `--boot-app0 PATH`.

The included `firmware/factory.bin` is 1,784,464 bytes with SHA-256 `0b6ed89aa897e18a2a94b9ae2334d50f698a68ce399a966f25d40726e9b6e71a`. The code is GPL-3.0-only; see [LICENSE](LICENSE). ESP Web Tools is loaded separately under its own Apache-2.0 license.
