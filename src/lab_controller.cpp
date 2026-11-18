/*
   SPDX-License-Identifier: GPL-3.0-or-later
*/
#include <Arduino.h>
#include <stdlib.h>
#include "glitcher.h"
#include "nrf_swd.h"
#include "lab_controller.h"

static String serial_command;

void lab_controller_begin()
{
  Serial.println("LAB_READY");
  Serial.println("LAB_HELP: START | STOP | STATUS | SET delay=<us> delay_end=<us> width=<us> power_off=<ms> swd_wait=<ms>");
}

static void print_status()
{
  Serial.printf(
      "LAB_STATUS enabled=%d delay_us=%lu delay_end_us=%lu width_us=%lu power_off_ms=%lu swd_wait_ms=%lu\r\n",
      get_glitcher() ? 1 : 0,
      (unsigned long)get_delay(),
      (unsigned long)get_delay_end(),
      (unsigned long)get_width(),
      (unsigned long)get_power_off_delay(),
      (unsigned long)get_swd_wait_delay());
}

static uint32_t parse_value(const String &command, const char *name)
{
  int name_index = command.indexOf(name);
  if (name_index < 0)
    return 0;

  int value_index = name_index + strlen(name);
  while (value_index < command.length() && command[value_index] == ' ')
    value_index++;
  if (value_index < command.length() && command[value_index] == '=')
  {
    value_index++;
    while (value_index < command.length() && command[value_index] == ' ')
      value_index++;
  }

  return command.substring(value_index).toInt();
}

static void process_command(String command)
{
  command.trim();
  command.toUpperCase();

  if (command == "START")
  {
    set_glitcher(true);
    Serial.println("LAB_OK START");
  }
  else if (command == "STOP")
  {
    set_glitcher(false);
    Serial.println("LAB_OK STOP");
  }
  else if (command == "STATUS")
  {
    print_status();
  }
  else if (command.startsWith("ADC "))
  {
    String original = command;
    uint32_t delay_us = original.indexOf("DELAY=") >= 0 ? parse_value(original, "DELAY=") : 2000;
    uint32_t width_us = original.indexOf("WIDTH=") >= 0 ? parse_value(original, "WIDTH=") : 10;
    uint32_t power_off_ms = original.indexOf("POWER_OFF=") >= 0 ? parse_value(original, "POWER_OFF=") : get_power_off_delay();
    uint32_t sample_period_us = original.indexOf("SAMPLE_US=") >= 0 ? parse_value(original, "SAMPLE_US=") : 10;
    uint32_t size = original.indexOf("SAMPLES=") >= 0 ? parse_value(original, "SAMPLES=") : 500;

    if (size > 2000)
      size = 2000;

    uint16_t *samples = (uint16_t *)calloc(size, sizeof(uint16_t));
    uint32_t *times = (uint32_t *)calloc(size, sizeof(uint32_t));
    if (!samples || !times)
    {
      free(samples);
      free(times);
      Serial.println("LAB_ADC_ERROR ALLOCATION");
      return;
    }

    get_osci_graph_timed(samples, times, size, delay_us, width_us, power_off_ms, sample_period_us);

    Serial.printf(
        "LAB_ADC_HEADER delay_us=%lu width_us=%lu power_off_ms=%lu sample_period_us=%lu samples=%lu\r\n",
        (unsigned long)delay_us,
        (unsigned long)width_us,
        (unsigned long)power_off_ms,
        (unsigned long)sample_period_us,
        (unsigned long)size);
    for (uint32_t i = 0; i < size; i++)
      Serial.printf("LAB_ADC time_us=%lu value=%u\r\n", (unsigned long)times[i], (unsigned int)samples[i]);
    Serial.println("LAB_ADC_END");
    free(samples);
    free(times);
  }
  else if (command.startsWith("SET "))
  {
    String original = command;
    int delay_index = original.indexOf("DELAY=");
    int delay_end_index = original.indexOf("DELAY_END=");
    int width_index = original.indexOf("WIDTH=");
    int power_off_index = original.indexOf("POWER_OFF=");
    int swd_wait_index = original.indexOf("SWD_WAIT=");

    uint32_t delay_us = delay_index >= 0 ? parse_value(original, "DELAY=") : get_delay();
    uint32_t delay_end_us = delay_end_index >= 0 ? parse_value(original, "DELAY_END=") : get_delay_end();
    uint32_t width_us = width_index >= 0 ? parse_value(original, "WIDTH=") : get_width();
    uint32_t power_off_ms = power_off_index >= 0 ? parse_value(original, "POWER_OFF=") : get_power_off_delay();
    uint32_t swd_wait_ms = swd_wait_index >= 0 ? parse_value(original, "SWD_WAIT=") : get_swd_wait_delay();

    set_delay(delay_us, delay_end_us, power_off_ms, swd_wait_ms);
    set_width(width_us);
    Serial.println("LAB_OK SET");
    print_status();
  }
  else
  {
    Serial.println("LAB_ERROR UNKNOWN_COMMAND");
  }
}

void lab_controller_poll()
{
  while (Serial.available())
  {
    char c = (char)Serial.read();
    if (c == '\r')
      continue;
    if (c == '\n')
    {
      process_command(serial_command);
      serial_command = "";
    }
    else if (serial_command.length() < 200)
    {
      serial_command += c;
    }
  }
}
