#pragma once
#include <stdint.h>
#define I2C_MAX_CMD_BYTES 10
typedef void (*I2C_lead_callback_t)(uint8_t,uint8_t,uint8_t*);
typedef int (*I2C_follow_callback_t)(uint8_t*);
typedef void (*I2C_error_callback_t)(int);
uint8_t I2C_Init(uint8_t,I2C_lead_callback_t,I2C_follow_callback_t,I2C_follow_callback_t,I2C_error_callback_t);
void I2C_DeInit(void);
void I2C_SetPullups(uint8_t);
uint8_t I2C_GetPullups(void);
uint8_t I2C_GetAddress(void);
void I2C_SetAddress(uint8_t);
int I2C_is_ready(void);
int I2C_LeadTx(uint8_t,uint8_t*,uint8_t);
int I2C_LeadRx(uint8_t,uint8_t*,uint8_t,uint8_t);
