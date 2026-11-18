/*
   Copyright (c) 2021 Aaron Christophel ATCnetz.de
   SPDX-License-Identifier: GPL-3.0-or-later
*/
#pragma once

void glitcher_begin();
void set_glitcher(bool new_state);
bool get_glitcher();
void set_power(bool state);
void do_glitcher();
void set_delay(uint32_t delay_us, uint32_t delay_us_end, uint32_t power_off_delay, uint32_t swd_wait_delay);
uint32_t get_delay();
uint32_t get_delay_end();
bool inc_delay();
void set_width(uint32_t width);
uint32_t get_width();
bool inc_width();
uint32_t get_power_off_delay();
uint32_t get_swd_wait_delay();

void get_osci_graph(uint16_t graph_buff[], uint32_t size, uint32_t delay_time);
void get_osci_graph_timed(
    uint16_t graph_buff[],
    uint32_t time_us_buff[],
    uint32_t size,
    uint32_t delay_time,
    uint32_t pulse_width,
    uint32_t power_off_delay,
    uint32_t sample_period_us);