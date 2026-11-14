package com.example.stepcounterapp;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity implements SensorEventListener {
    private static final int ACTIVITY_PERMISSION_CODE = 100;

    private SensorManager sensorManager;
    private Sensor stepSensor;
    private TextView stepsText, goalText, distanceText, caloriesText;
    private ProgressBar progressBar;
    private Button resetButton;
    private Spinner goalSpinner;
    
    private SharedPreferences preferences;
    private float initialSteps = -1;
    private int todaySteps = 0;
    
    // Prize logic
    private int currentGoal = 5000;
    private boolean prizeClaimed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize UI
        stepsText = findViewById(R.id.stepsText);
        goalText = findViewById(R.id.goalText);
        distanceText = findViewById(R.id.distanceText);
        caloriesText = findViewById(R.id.caloriesText);
        progressBar = findViewById(R.id.progressBar);
        resetButton = findViewById(R.id.resetButton);
        goalSpinner = findViewById(R.id.goalSpinner);

        preferences = getSharedPreferences("StepChecker", MODE_PRIVATE);
        initialSteps = preferences.getFloat("initialSteps", -1);
        prizeClaimed = preferences.getBoolean("prizeClaimed", false);
        
        // Setup Goal Spinner
        String[] goals = {"5,000 Steps (Coffee Voucher)", "10,000 Steps (Meal Voucher)", "15,000 Steps (Shopping Voucher)"};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, goals);
        goalSpinner.setAdapter(adapter);

        // Restore selected goal
        int savedGoalIndex = preferences.getInt("goalIndex", 0);
        goalSpinner.setSelection(savedGoalIndex);
        updateGoal(savedGoalIndex);

        goalSpinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> parent, android.view.View view, int position, long id) {
                updateGoal(position);
                preferences.edit().putInt("goalIndex", position).apply();
            }
            @Override
            public void onNothingSelected(android.widget.AdapterView<?> parent) {}
        });

        resetButton.setOnClickListener(v -> {
            initialSteps = -1;
            todaySteps = 0;
            prizeClaimed = false;
            preferences.edit()
                    .remove("initialSteps")
                    .putBoolean("prizeClaimed", false)
                    .apply();
            Toast.makeText(MainActivity.this, "Step counter and prize reset", Toast.LENGTH_SHORT).show();
            updateUI();
        });
        
        sensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        stepSensor = sensorManager.getDefaultSensor(Sensor.TYPE_STEP_COUNTER);

        checkActivityPermission();
        updateUI();
    }

    private void updateGoal(int position) {
        if (position == 0) currentGoal = 5000;
        else if (position == 1) currentGoal = 10000;
        else currentGoal = 15000;
        
        progressBar.setMax(currentGoal);
        goalText.setText("Goal: " + currentGoal + " steps");
        updateUI();
    }

    private void updateUI() {
        stepsText.setText(String.valueOf(todaySteps));
        progressBar.setProgress(Math.min(todaySteps, currentGoal));

        double distanceKm = (todaySteps * 0.75) / 1000;
        distanceText.setText(String.format("Distance: %.2f km", distanceKm));

        double calories = todaySteps * 0.04;
        caloriesText.setText(String.format("Calories: %.0f kcal", calories));

        // Check for Prize
        if (todaySteps >= currentGoal && !prizeClaimed) {
            prizeClaimed = true;
            preferences.edit().putBoolean("prizeClaimed", true).apply();
            showPrizeDialog();
        }
    }

    private void showPrizeDialog() {
        new AlertDialog.Builder(this)
                .setTitle("🎉 CONGRATULATIONS!")
                .setMessage("You reached " + currentGoal + " steps!\n\nYou have won a voucher! Keep up the great work.")
                .setPositiveButton("Claim Prize", (dialog, which) -> {
                    Toast.makeText(this, "Voucher saved to your account!", Toast.LENGTH_LONG).show();
                })
                .setCancelable(false)
                .show();
    }

    private void checkActivityPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACTIVITY_RECOGNITION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.ACTIVITY_RECOGNITION}, ACTIVITY_PERMISSION_CODE);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (stepSensor != null && ContextCompat.checkSelfPermission(this, Manifest.permission.ACTIVITY_RECOGNITION) == PackageManager.PERMISSION_GRANTED) {
            sensorManager.registerListener(this, stepSensor, SensorManager.SENSOR_DELAY_UI);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (sensorManager != null) sensorManager.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() == Sensor.TYPE_STEP_COUNTER) {
            float totalSensorSteps = event.values[0];
            if (initialSteps < 0) {
                initialSteps = totalSensorSteps;
                preferences.edit().putFloat("initialSteps", initialSteps).apply();
            }
            todaySteps = (int) (totalSensorSteps - initialSteps);
            if (todaySteps < 0) todaySteps = 0;
            updateUI();
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == ACTIVITY_PERMISSION_CODE && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this, "Permission granted", Toast.LENGTH_SHORT).show();
        }
    }
}