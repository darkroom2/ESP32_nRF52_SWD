/*
   Copyright (c) 2021 Aaron Christophel ATCnetz.de
   SPDX-License-Identifier: GPL-3.0-or-later
*/
#include <Arduino.h>
#include "defines.h"
#include "swd.h"
#include "nrf_swd.h"
#include "glitcher.h"

#define delay_inc_step 1
#define width_inc_step 1

uint32_t delay_max = 30000;
uint32_t width_max = 30;

uint32_t delay_start = 2000;
uint32_t width_start = 0;

uint32_t _delay_us = 0;
uint32_t _delay_us_end = 0;
uint32_t _width = 0;

uint32_t _power_off_delay = 50;
uint32_t _swd_wait_delay = 100;

bool glitcher_enabled = false;
uint32_t lab_attempt = 0;

void glitcher_begin()
{
  _delay_us = delay_start;
  _delay_us_end = delay_max;
  _width = width_start;
  pinMode(LED, OUTPUT);
  pinMode(GLITCHER, OUTPUT);
  pinMode(NRF_POWER, OUTPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(OSCI_PIN, ADC_11db);
  digitalWrite(GLITCHER, LOW);
  set_power(HIGH);
}

void set_glitcher(bool new_state)
{
  glitcher_enabled = new_state;
}

bool get_glitcher()
{
  return glitcher_enabled;
}

#ifndef LED_STATE_ON
#define LED_STATE_ON HIGH
#endif

void set_power(bool state)
{
  digitalWrite(NRF_POWER, state);
  digitalWrite(LED, LED_STATE_ON ? state : !state);
}

void do_glitcher()
{
  lab_attempt++;
  Serial.printf(
      "LAB_ATTEMPT id=%lu delay_us=%lu width_us=%lu power_off_ms=%lu swd_wait_ms=%lu\r\n",
      (unsigned long)lab_attempt,
      (unsigned long)get_delay(),
      (unsigned long)get_width(),
      (unsigned long)_power_off_delay,
      (unsigned long)_swd_wait_delay);

  digitalWrite(swd_clock_pin, LOW);
  set_power(LOW);
  delay(_power_off_delay);
  set_power(HIGH);
  delayMicroseconds(get_delay());
  digitalWrite(GLITCHER, HIGH);
  delayMicroseconds(get_width());
  digitalWrite(GLITCHER, LOW);

  if (inc_width())
  {
    inc_delay();
  }

  delay(_swd_wait_delay);
  uint32_t swd_id = nrf_begin(true);
  uint32_t variant_read = read_register(0x10000100);
  bool unlocked = nrf_read_lock_state();
  bool success = variant_read == 0x00052832 || variant_read == 0x00052840 || unlocked;

  Serial.printf(
      "LAB_RESULT id=%lu swd=0x%08x variant=0x%08x unlocked=%d success=%d\r\n",
      (unsigned long)lab_attempt,
      (unsigned int)swd_id,
      (unsigned int)variant_read,
      unlocked ? 1 : 0,
      success ? 1 : 0);

  if (success)
  {
    Serial.println("We Have a good glitch");
    glitcher_enabled = false;
    Serial.printf("SWD Id: 0x%08x\r\n", nrf_begin());
  }
}

void set_delay(uint32_t delay_us, uint32_t delay_us_end, uint32_t power_off_delay, uint32_t swd_wait_delay)
{
  _delay_us = delay_us;
  delay_start = _delay_us;

  _delay_us_end = delay_us_end;
  delay_max = _delay_us_end;

  _power_off_delay = power_off_delay;
  _swd_wait_delay = swd_wait_delay;
}

uint32_t get_delay()
{
  return _delay_us;
}

uint32_t get_delay_end()
{
  return _delay_us_end;
}

uint32_t get_power_off_delay()
{
  return _power_off_delay;
}

uint32_t get_swd_wait_delay()
{
  return _swd_wait_delay;
}

bool inc_delay()
{
  _delay_us += delay_inc_step;
  if (_delay_us > _delay_us_end)
  {
    _delay_us = delay_start;
    return true;
  }
  return false;
}

void set_width(uint32_t width)
{
  _width = width;
  width_start = width;
  width_max = width;
}

uint32_t get_width()
{
  return _width;
}

bool inc_width()
{
  _width += width_inc_step;
  if (_width > width_max)
  {
    _width = width_start;
    return true;
  }
  return false;
}

void get_osci_graph(uint16_t graph_buff[], uint32_t size, uint32_t delay_time)
{
  digitalWrite(swd_clock_pin, LOW);
  set_power(LOW);
  delay(_power_off_delay);
  set_power(HIGH);
  long start_micro = micros();
  bool has_fired = 0;
  for (int i = 0; i < size; i++)
  {
    if (!has_fired && micros() - start_micro > delay_time)
    {
      has_fired = 1;
      digitalWrite(GLITCHER, HIGH);
      graph_buff[i++] = analogRead(OSCI_PIN);
      digitalWrite(GLITCHER, LOW);
    }
    graph_buff[i] = analogRead(OSCI_PIN);
  }
}

void get_osci_graph_timed(
    uint16_t graph_buff[],
    uint32_t time_us_buff[],
    uint32_t size,
    uint32_t delay_time,
    uint32_t pulse_width,
    uint32_t power_off_delay,
    uint32_t sample_period_us)
{
  digitalWrite(swd_clock_pin, LOW);
  set_power(LOW);
  delay(power_off_delay);
  set_power(HIGH);

  uint32_t start_us = micros();
  bool has_fired = false;

  for (uint32_t i = 0; i < size; i++)
  {
    uint32_t elapsed_us = micros() - start_us;
    if (pulse_width > 0 && !has_fired && elapsed_us >= delay_time)
    {
      has_fired = true;
      digitalWrite(GLITCHER, HIGH);
    }

    time_us_buff[i] = elapsed_us;
    graph_buff[i] = analogRead(OSCI_PIN);

    if (has_fired && elapsed_us >= delay_time + pulse_width)
    {
      digitalWrite(GLITCHER, LOW);
    }

    if (sample_period_us > 0)
      delayMicroseconds(sample_period_us);
  }

  digitalWrite(GLITCHER, LOW);
  set_power(HIGH);
}
