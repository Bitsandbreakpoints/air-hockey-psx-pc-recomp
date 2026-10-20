/*
 * hle_pad.c - LIBPAD: the controllers.
 *
 * As on the PS1, the replies of both controllers are written into the
 * game's buffers at every vertical blank (PadInitDirect() mode): status
 * byte (0 = connected), type (0x41: digital pad) and the 16 button bits,
 * active low.  The buttons come from the PC side (psx_set_pad_reader():
 * keyboard / XInput after the settings).  Vibration is not supported.
 */
#include "runtime/recomp.h"
#include "runtime/runtime.h"
#include "runtime/system.h"
#include "runtime/irq.h"

#define PAD_PORTS               2
#define PAD_STATUS_OK           0x00
#define PAD_STATUS_NONE         0xFF
#define PAD_TYPE_DIGITAL        0x41    /* 4 bits: type, 4 bits: half-words of data */

static uint32_t s_buffers[PAD_PORTS];
static int s_running;
static PsxPadReader s_reader;

void psx_set_pad_reader(PsxPadReader reader)
{
    s_reader = reader;
}

void pad_reset(void)
{
    s_buffers[0] = s_buffers[1] = 0;
    s_running = 0;
}

static void write_reply(uint32_t buffer, int buttons)
{
    if (buttons < 0) {
        WR8(buffer, PAD_STATUS_NONE);
        WR8(buffer + 2, 0xFF);
        WR8(buffer + 3, 0xFF);
    } else {
        WR8(buffer, PAD_STATUS_OK);
        WR8(buffer + 1, PAD_TYPE_DIGITAL);
        WR8(buffer + 2, (uint8_t) ~buttons);
        WR8(buffer + 3, (uint8_t) (~buttons >> 8));
    }
}

/* at every vertical blank */
void pad_update(void)
{
    if (!s_running) {
        return;
    }
    for (int port = 0; port < PAD_PORTS; port++) {
        if (s_buffers[port]) {
            write_reply(s_buffers[port], s_reader ? s_reader(port) : -1);
        }
    }
}

void hle_PadInitDirect(void)
{
    s_buffers[0] = GPR[4];
    s_buffers[1] = GPR[5];
    for (int port = 0; port < PAD_PORTS; port++) {
        if (s_buffers[port]) {
            write_reply(s_buffers[port], -1);
        }
    }
    RETURN(1);
}

void hle_PadStartCom(void)
{
    s_running = 1;
    RETURN(1);
}

void hle_PadStopCom(void)
{
    s_running = 0;
    RETURN(1);
}
